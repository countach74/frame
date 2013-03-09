#!/usr/bin/python

import socket
import threading
from headers import RequestHeaders, RequestLine
import modulemonitor
import signal
import sys
import os
import traceback
import cgi
from jinja2 import Environment, PackageLoader, ChoiceLoader, FileSystemLoader
from StringIO import StringIO

# Needed for asynchronous server
import select

# Logger stuff
from frame import logger


def parse_body(request):
	try:
		return request.split('\r\n\r\n', 1)[1]
	except IndexError:
		return ''


class Connection(object):
	def __init__(self, server, accept):
		self.server = server
		self.socket, self.addr = accept

		self.read_buffer = []
		self.write_buffer = []
		
		self.total_received = 0
		self.request_body_received = 0
		self.request_body_length = None
		self.request_headers = None

	def fileno(self):
		return self.socket.fileno()

	def handle_connect(self):
		pass

	def handle_read(self):
		try:
			data = self.socket.recv(self.server.chunk_size)
		except socket.error:
			self.close()
			return
			
		self.total_received += len(data)
		self.read_buffer.append(data)
		last_two_chunks = ''.join(self.read_buffer[-2:])
		
		if '\r\n\r\n' in last_two_chunks and not self.request_headers:
			raw_request = ''.join(self.read_buffer).split('\r\n\r\n', 1)
			self.request_body_received += len(raw_request[1])
			self.request_headers = RequestHeaders(raw_request[0])
			
			try:
				self.request_body_length = int(self.request_headers['HTTP_CONTENT_LENGTH'])
			except (KeyError, ValueError):
				self.request_body_length = 0
			finally:
				if self.request_body_received >= self.request_body_length:
					if self in self.server.r_list:
						self.server.r_list.remove(self)
					request = ''.join(self.read_buffer)
					self.handle_request(request)
					
		elif self.request_headers:
			self.request_body_received += len(data)
			if self.request_body_received >= self.request_body_length:
				if self in self.server.r_list:
					self.server.r_list.remove(self)
				request = ''.join(self.read_buffer)
				self.handle_request(request)

	def handle_write(self):
		data = self.write_buffer.pop(0)
		try:
			self.socket.send(data)
		except socket.error:
			self.close()

		if not self.write_buffer:
			self.close()

	def handle_request(self, request):
		if not request:
			self.close()
			return

		request_body = parse_body(request)
		
		wsgi_environ = {
			'wsgi.multiprocess': False,
			'wsgi.url_scheme': 'http',
			'wsgi.input': StringIO(request_body),
			'wsgi.multithread': True,
			'wsgi.version': (1, 0),
			'wsgi.run_once': False,
			'wsgi.errors': ''
		}

		try:
			uri_headers = RequestLine(request)
		except ValueError:
			self.close()
			return

		other_headers = {
			'SERVER_ADDR': self.server.host,
			'SERVER_PORT': self.server.port,
			'SERVER_NAME': self.server.host,
			'SERVER_PROTOCOL': 'HTTP/1.1',
			'SERVER_SOFTWARE': 'Frame/0.1a',
			'REMOTE_ADDR': self.addr[0],
			'REMOTE_PORT': self.addr[1],
			'GATEWAY_INTERFACE': 'CGI/1.1',
			'SCRIPT_FILENAME': os.path.abspath(sys.argv[0]),
			'DOCUMENT_ROOT': os.getcwd() + '/',
			'PATH_TRANSLATED': os.getcwd() + '/' + uri_headers['PATH_INFO'],
			'SCRIPT_NAME': '',
			'REDIRECT_STATUS': 200
		}

		all_headers = dict(self.request_headers.items() + wsgi_environ.items() +
			other_headers.items() + uri_headers.items())

		try:
			response = self.server.app(all_headers, self.start_response)
		except Exception, e:
			response = []
			self.status = '500 Internal Server Error'
			self.headers = [('Content-Type', 'text/html')]

			e_type, e_value, e_tb = sys.exc_info()
			tb = traceback.format_exception(e_type, e_value, e_tb)

			response.append(
				self.server.environment.get_template('traceback.html').render(traceback=tb))

		finally:
			# Send headers
			headers_sent = False
			
			# Send response
			for i in response:
				if not headers_sent:
					self.send_headers(self.status, self.headers)
					headers_sent = True
				self.send(i)

	def send_headers(self, status, headers):
		self.send("HTTP/1.1 %s\r\n" % status)
		for k, v in headers:
			self.send("%s: %s\r\n" % (k, v))
		self.send("\r\n")

	def start_response(self, status, headers, other=None):
		self.status = status
		self.headers = headers
		self.other = other

	def send(self, data):
		self.write_buffer.append(data)

		# Make sure connection is part of the write list
		if self not in self.server.w_list:
			self.server.w_list.append(self)

	def shutdown(self):
		self.socket.shutdown(socket.SHUT_RDWR)

	def close(self):
		self.socket.close()
		if self in self.server.r_list:
			self.server.r_list.remove(self)
		if self in self.server.w_list:
			self.server.w_list.remove(self)


class HTTPServer(object):
	def __init__(self, app, host='localhost', port=8080, listen=5, max_read=8092, chunk_size=1024, auto_reload=True):
		self.app = app
		self.host = host
		self.port = port
		self.listen = listen
		self.chunk_size = chunk_size
		self.max_read = max_read
		self.auto_reload = auto_reload

		self.connections = []

		# Setup socket
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		if self.auto_reload:
			self.module_monitor = modulemonitor.ModuleMonitor(self)

		self.environment = Environment(
			loader=ChoiceLoader([PackageLoader('frame', 'templates'),
				FileSystemLoader('templates')]))

		self.running = True

		# Basic lists needed for select
		self.r_list = [self.socket]
		self.w_list = []
		self.e_list = []

	def bind_socket(self):
		self.socket.bind((self.host, self.port))
		self.socket.listen(self.listen)

	def _handle_signal(self, signum, frame):
		if signum in (signal.SIGTERM, signal.SIGINT):
			self.stop(True)

	def setup_signal_handlers(self):
		signal.signal(signal.SIGTERM, self._handle_signal)
		signal.signal(signal.SIGINT, self._handle_signal)

	def run(self):
		self.bind_socket()
		self.setup_signal_handlers()
		
		if self.auto_reload:
			self.module_monitor.start()
		
		while self.running:
			try:
				r_ready, w_ready, e_ready = select.select(self.r_list, self.w_list, self.e_list)
			except select.error:
				r_ready, w_ready, e_ready = [], [], []
				self.running = False

			for i in r_ready:
				if i is self.socket:
					connection = Connection(self, self.socket.accept())
					self.r_list.append(connection)
					connection.handle_connect()

				elif isinstance(i, Connection):
					i.handle_read()

			for i in w_ready:
				i.handle_write()

			for i in e_ready:
				i.handle_error()
				
	def stop(self, stop_monitor=False):
		logger.log_info("Shutting down Frame HTTP Server...")
		
		for i in self.connections:
			i.shutdown()
			i.close()
			i.join()

		self.socket.shutdown(socket.SHUT_RDWR)
		self.socket.close()

		if stop_monitor and self.auto_reload:
			self.module_monitor.stop()
			self.module_monitor.join()

		for i in threading.enumerate():
			if isinstance(i, Connection):
				i.shutdown()
				i.close()
				i.join()