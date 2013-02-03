from _request import Request
from _response import Response
from _routes import routes
from _dotdict import DotDict
from errors import HTTPError
import traceback
from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader
import os
import sys
import sessions


class App(object):
	def __init__(self, static_dir='/static', template_dir='templates', debug=False):
		self.static_dir = static_dir
		self._template_dir = template_dir
		self.path = os.path.dirname(os.path.abspath(sys.argv[0]))
		self.routes = routes
		self.debug = debug

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

		# Setup session interface
		self.session_interface = sessions.SessionInterface(self)

	@property
	def template_dir(self):
		return self._template_dir

	@template_dir.setter
	def template_dir(self, value):
		self._template_dir = value
		self.environment = Environment(FileSystemLoader(value))

	def _dispatch(self, environ):
		self.request = Request(environ)

		try:
			match, data = routes.match(environ=environ)

		# If TypeError or AttributeError occurs then no match was found; we should throw a 404.
		except (TypeError, AttributeError):
			status = '404 Not Found'
			headers = {'Content-Type': 'text/html'}
			response_body = self.environment.get_template('errors/404.html').render(
				path=environ['REQUEST_URI'],
				title='404 Not Found')

		# Otherwise, we should be good to handle the request
		else:
			for key, value in data.items():
				if key in ('controller', 'action', 'method'):
					del(data[key])

			try:
				self.response = Response(match)
			except HTTPError, e:
				status = e.status
				headers = e.headers
				response_body = e.body
			else:
				self.session = self.session_interface.get_session()
				response_body = self.response.render(self.request.fcgi.query_string, data)

				# Save the session before yielding the response
				self.session_interface.save_session(self.session)

				status = self.response.status
				headers = self.response.headers

		return (status, headers, response_body)

	def __call__(self, environ, start_response):
		# debug mode gets set to true if start_http() is used.
		if self.debug:
			status, headers, response_body = self._dispatch(environ)
		else:
			try:
				status, headers, response_body = self._dispatch(environ)
			except Exception, e:
				status = '500 Internal Server Error'
				headers = {'Content-Type': 'text/html'}

				e_type, e_value, e_tb = sys.exc_info()
				tb = traceback.format_exception(e_type, e_value, e_tb)

				response_body = self.environment.get_template('errors/500.html').render(title='500 Internal Server Error')

		for i in self.post_processors:
			headers, response_body = i(self.request, headers, str(response_body))

		response_body = str(response_body)
		headers['Content-Length'] = str(len(response_body))

		# Deliver the goods
		start_response(status, headers.items())
		yield response_body

	def start_fcgi(self, debug=False, *args, **kwargs):
		self.debug = debug

		from flup.server.fcgi import WSGIServer
		WSGIServer(self).run(*args, **kwargs)

	def start_http(self, debug=True, *args, **kwargs):
		self.debug = debug

		from frame.server.http import HTTPServer
		HTTPServer(self).run(*args, **kwargs)


app = App()
