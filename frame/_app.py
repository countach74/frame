from _request import Request
from _response import Response
from _routes import routes
from _dotdict import DotDict
from errors import HTTPError, Error404, Error500
import traceback
from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader
import os
import sys
import sessions
import mimetypes
import types

# For jinja2 toolset
from toolset import toolset

# Import default preprocessors
from preprocessors import form_url_encoder, form_ajax
from partialviews import PartialViews

# Needed for loading ORM drivers
import orm
import orm.datatypes
import forms

# Import StaticDispatcher to retrieve static files
from staticdispatcher import StaticDispatcher


__frame_path = os.path.dirname(os.path.abspath(__file__))

_default_static_map = {
	'/static': 'static',
	'/static/frame': os.path.join(__frame_path, 'static')
}


class App(object):
	def __init__(self, template_dir='templates', debug=True, static_map=_default_static_map):
		self.static_map = StaticDispatcher(static_map)
		self._template_dir = template_dir
		self.path = os.path.dirname(os.path.abspath(sys.argv[0]))
		self.routes = routes
		self.debug = debug

		self.pre_processors = [form_url_encoder, form_ajax]
		self.post_processors = []

		self.config = DotDict()
		self.config.sessions = {
			'enabled': True,
			'key_name': 'FrameSession',
			'expires': 168,  #Set session expiration to 1 week by default
		}

		# Setup Jinja2 environment
		self.environment = Environment(loader=ChoiceLoader([
			FileSystemLoader(template_dir),
			PackageLoader('frame', 'templates')]))

		self.toolset = toolset
		self.toolset.app = self

		# Setup partial views object
		self.partial_views = PartialViews(self)

		# Setup session interface
		self.session_interface = sessions.SessionInterface(self)

		# Get ORM drivers
		forms.BasicForm._environment = self.environment
		orm.datatypes.CustomType._environment = self.environment
		self.orm_drivers = orm.available_drivers
		self._orm = 'mongo'

	@property
	def template_dir(self):
		return self._template_dir

	@template_dir.setter
	def template_dir(self, value):
		self._template_dir = value
		self.environment = Environment(loader=ChoiceLoader([
			FileSystemLoader(value),
			PackageLoader('frame', 'templates')]))

	@property
	def orm(self):
		return self.orm_drivers[self._orm]

	@orm.setter
	def orm(self, value):
		orm.active_driver = value
		self._orm = value

	@property
	def Connection(self):
		return self.orm.Connection

	def _dispatch(self, environ):
		self.request = Request(environ)

		try:
			match, data = routes.match(environ=environ)

		# If TypeError or AttributeError occurs then no match was found; we should throw a 404.
		except (TypeError, AttributeError):
			return self.static_map.match(environ)

		# Otherwise, we should be good to handle the request
		else:
			for key, value in data.items():
				if key in ('controller', 'action', 'method'):
					del(data[key])

			try:
				self.response = Response(self, match)
			except HTTPError, e:
				status = e.status
				headers = e.headers
				response_body = e.body
			else:
				try:
					self.session = self.session_interface.get_session()
				except Exception, e:
					raise Error500

				self.environment.globals['session'] = self.session
				self.environment.globals['tools'] = self.toolset

				# Cool trick to make 'session' available everywhere easily
				sys.modules['session'] = self.session

				for i in self.pre_processors:
					i(self.request, self.response)

				try:
					response_body = self.response.render(self.request.headers.query_string, data)
				except HTTPError, e:
					raise e
				except Exception, e:
					raise Error500

				# Save the session before yielding the response
				try:
					self.session_interface.save_session(self.session)
				except Exception, e:
					raise Error500

				status = self.response.status
				headers = self.response.headers

		return (status, headers, response_body)

	def __call__(self, environ, start_response):
		# debug mode gets set to true if start_http() is used.
		#if self.debug:
		#	status, headers, response_body = self._dispatch(environ)
		#else:
		try:
			status, headers, response_body = self._dispatch(environ)
		except HTTPError, e:
			status, headers, response_body = e.render(self)

		if type(response_body) is types.GeneratorType:
			headers['Transfer-Encoding'] = 'chunked'
			start_response(status, headers.items())
			for i in response_body:
				yield "%0X\r\n%s\r\n" % (len(i), i)
			yield "0\r\n\r\n"

		else:
			# Apply post processors
			for i in self.post_processors:
				headers, response_body = i(self.request, headers, str(response_body))

			response_body = str(response_body)
			headers['Content-Length'] = str(len(response_body))

			# Deliver the goods
			start_response(status, headers.items())
			yield response_body

	def start_fcgi(self, *args, **kwargs):
		from flup.server.fcgi import WSGIServer
		WSGIServer(self, *args, **kwargs).run()

	def start_http(self, *args, **kwargs):
		from frame.server.http import HTTPServer
		HTTPServer(self, *args, **kwargs).run()

	def start_wsgi(self, host='127.0.0.1', port=8080, *args, **kwargs):
		from wsgiref.simple_server import make_server
		httpd = make_server(host, port, self, *args, **kwargs)
		httpd.serve_forever()


app = App()
