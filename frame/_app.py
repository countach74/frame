from _request import Request
from _response import Response
from _routes import routes
from errors import HTTPError
import traceback
from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader
import os
import sys


class App(object):
	def __init__(self, static_dir='/static', template_dir='templates', debug=False):
		self.static_dir = static_dir
		self._template_dir = template_dir
		self.path = os.path.dirname(os.path.abspath(sys.argv[0]))
		self.routes = routes
		self.debug = debug

		# Setup Jinja2 environment
		self.environment = Environment(loader=ChoiceLoader([
			FileSystemLoader(template_dir),
			PackageLoader('frame', 'templates')]))

	@property
	def template_dir(self):
		return self._template_dir

	@template_dir.setter
	def template_dir(self, value):
		self._template_dir = value
		self.environment = Environment(FileSystemLoader(value))

	def __dispatch(self, environ, start_response):
		self.request = Request(environ)

		try:
			match, data = routes.match(environ=environ)

		# If TypeError occurs then no match was found; we should throw a 404.
		except TypeError:
			start_response('404 Not Found', [('Content-Type', 'text/html')])
			yield self.environment.get_template('errors/404.html').render(path=environ['REQUEST_URI'], title='404 Not Found')
			raise StopIteration

		for key, value in data.items():
			if key in ('controller', 'action', 'method'):
				del(data[key])

		try:
			self.response = Response(start_response, match)
		except HTTPError, e:
			start_response(e.status, e.headers)
			yield e.body
		else:
			yield self.response.render(self.request.fcgi.query_string, data)

	def __call__(self, environ, start_response):
		if self.debug:
			for i in self.__dispatch(environ, start_response):
				yield i
		else:
			try:
				for i in self.__dispatch(environ, start_response):
					yield i
			except Exception, e:
				start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
				e_type, e_value, e_tb = sys.exc_info()
				tb = traceback.format_exception(e_type, e_value, e_tb)
				yield self.environment.get_template('errors/500.html').render(title='500 Internal Server Error')

	def start_fcgi(self):
		from flup.server.fcgi import WSGIServer
		WSGIServer(self).run()

	def start_http(self):
		from frame.server.http import HTTPServer
		HTTPServer(self).run()


app = App()
