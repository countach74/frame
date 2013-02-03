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

# Needed for asynchronous server
import select


class Connection(object):
	def __init__(self, server, accept):
		self.server = server
		self.socket, self.addr = accept

		self.read_buffer = []
		self.write_buffer = []

	def fileno(self):
		return self.socket.fileno()

	def handle_connect(self):
		pass

	def handle_read(self):
		request = self.socket.recv(self.server.max_read)
		self.handle_request(request)

	def handle_write(self):
		data = self.write_buffer.pop(0)
		try:
			self.socket.send(data)
		except socket.error:
			print "UHOH"

		if not self.write_buffer:
			self.server.w_list.remove(self)
			self.close()

	def handle_request(self, request):
		if not request:
			self.close()
			return

		request_headers = RequestHeaders(request)
		wsgi_environ = {
			'wsgi.multiprocess': False,
			'wsgi.url_scheme': 'http',
			'wsgi.input': '',
			'wsgi.multithread': True,
			'wsgi.version': (1, 0),
			'wsgi.run_once': False,
			'wsgi.errors': ''
		}

		uri_headers = RequestLine(request)

		other_headers = {
			'SERVER_ADDR': self.server.host,
			'SERVER_PORT': self.server.port,
			'SERVER_NAME': self.server.host,
			'SERVER_PROTOCOL': 'HTTP/1.1',
			'SERVER_SOFTWARE': 'poopyd/0.1a',
			'REMOTE_ADDR': self.addr[0],
			'REMOTE_PORT': self.addr[1],
			'GATEWAY_INTERFACE': 'CGI/1.1',
			'SCRIPT_FILENAME': os.path.abspath(sys.argv[0]),
			'DOCUMENT_ROOT': os.getcwd() + '/',
			'PATH_TRANSLATED': os.getcwd() + '/' + uri_headers['PATH_INFO'],
			'SCRIPT_NAME': '',
			'REDIRECT_STATUS': 200
		}

		all_headers = dict(request_headers.items() + wsgi_environ.items() + other_headers.items() + uri_headers.items())

		response = []

		try:
			response.extend(self.server.app(all_headers, self.start_response))
		except Exception, e:
			self.status = '500 Internal Server Error'
			self.headers = [('Content-Type', 'text/html')]

			e_type, e_value, e_tb = sys.exc_info()
			tb = traceback.format_exception(e_type, e_value, e_tb)

			response.append(
				self.server.environment.get_template('traceback.html').render(traceback=tb))

		finally:
			# Send headers
			self.send_headers(self.status, self.headers)

			# Send response
			for i in response:
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
	def __init__(self, app, host='localhost', port=8080, listen=5, max_read=8092, auto_reload=False):
		self.app = app
		self.host = host
		self.port = port
		self.listen = listen
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
			sys.stderr.write("Shutting down...\n")
			self.stop(True)

	def setup_signal_handlers(self):
		signal.signal(signal.SIGTERM, self._handle_signal)
		signal.signal(signal.SIGINT, self._handle_signal)

	def run(self):
		self.bind_socket()
		self.setup_signal_handlers()

		while self.running:
			r_ready, w_ready, e_ready = select.select(self.r_list, self.w_list, self.e_list)

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
		self.running = False

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
