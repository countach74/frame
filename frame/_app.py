from request import Request
from response import Response
from _routes import routes
from dotdict import DotDict
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
#from preprocessors import form_url_encoder, form_json_encoder, form_multipart_encoder

from partialviews import PartialViews

# Needed for loading ORM drivers
import orm
import orm.datatypes
import forms

# Import StaticDispatcher to retrieve static files
from staticdispatcher import StaticDispatcher

# Import global config
from _config import config

# Import logger
from _logger import logger
from util import truncate, Singleton


class App(Singleton):
	'''
	The backbone behind Frame's dispatching. :class:`App` is a WSGI compliant application
	that handles all of the request/response sent to and generated by the application.
	Currently, it is also in charge of dispatching URI's to controllers/actions, but that
	may change in the future.
	
	There shouldn't be a lot of reason to interact directly with objects of this class,
	as most configuration options can be (and should be) set via :obj:`frame._config.config`.
	However, if you need to make some modifications to the Jinja2 environment or other
	hacking, this is the place to do it.
	'''
	
	def __init__(self, template_dir='templates', debug=True):
		'''
		Initialize the application with some sane defaults.
		'''
		
		self.static_map = StaticDispatcher(self)
		self._template_dir = template_dir
		self.path = os.path.dirname(os.path.abspath(sys.argv[0]))
		self.routes = routes
		self.debug = debug

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
		
		# Setup pre and post processor lists
		self.pre_processors = []
		self.post_processors = []

		# Setup ORM stuff
		forms.BasicForm._environment = self.environment
		orm.datatypes.CustomType._environment = self.environment
		self.orm_drivers = orm.available_drivers
		
	@property
	def template_dir(self):
		'''
		Retrieve or set the Jinja2 template directory. When setting, automatically reloads
		the Jinja2 environment using a :mod:`jinja2.ChoiceLoader` to provide fallback
		templates provided by Frame.
		'''
		return self._template_dir

	@template_dir.setter
	def template_dir(self, value):
		self._template_dir = value
		self.environment = Environment(loader=ChoiceLoader([
			FileSystemLoader(value),
			PackageLoader('frame', 'templates')]))

	@property
	def orm(self):
		return self.orm_drivers[config.orm.driver]

	@property
	def Connection(self):
		return self.orm.Connection
		
	@property
	def current_controller(self):
		'''
		Return the active :mod:`frame.controller.Controller`.
		'''
		return self.routes.current_controller

	def _dispatch(self, environ):
		'''
		Dispatches the HTTP request. Fetches the appropriate controller and action (if any)
		and instantiates :mod:`frame.request.Request`, :mod:`frame.response.Response`, and
		:mod:`frame.session.Session`. If any error is received while loading the controller
		action, an :exc:`frame.errors.Error500` exception is thrown and rendered neatly
		to the screen. If debugging is enabled, a traceback is sent as an HTTP response.
		
		:param environ: WSGI environment
		:return: A tuple of data to pass on to the WSGI server. The tuple consists of
			``(status_line, headers, response_body)``
		'''
		
		self.request = Request(environ)
		
		if config.application.strip_trailing_slash and environ['PATH_INFO'] != '/':
			environ['PATH_INFO'] = environ.get('PATH_INFO', '').rstrip('/')

		try:
			match, data = routes.match(environ=environ)

		# If TypeError or AttributeError occurs then no match was found; we should throw a 404.
		except (TypeError, AttributeError):
			return self.static_map.match(environ)
			
		# Any other errors are unexpected
		except Exception, e:
			raise Error500

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
					
				def save_session():
					try:
						self.session_interface.save_session(self.session)
					except Exception, e:
						raise Error500

				try:
					response_body = self.response.render(self.request.headers.query_string, data)
				except HTTPError, e:
					save_session()
					raise e
				except Exception, e:
					raise Error500

				# Save the session before yielding the response
				save_session()

				status = self.response.status
				headers = self.response.headers

		return (status, headers, response_body)

	def __call__(self, environ, start_response):
		'''
		A callable to allow WSGI compliance.
		
		:param environ: WSGI environment
		:param start_response: The start_response function passed by the WSGI server
		:yield: Response body
		'''
		
		try:
			status, headers, response_body = self._dispatch(environ)
		except HTTPError, e:
			status, headers, response_body = e.render(self)

		# Need to do something more elegant to handle generators/chunked encoding...
		# Also need to come up with a better way to log chunked encodings
		if type(response_body) is types.GeneratorType:
			start_response(status, headers.items())
			response_length = 0
			for i in response_body:
				yield i
				response_length += len(i)
			logger.log_request(self.request, self.response, response_length)

		else:
			# Apply post processors
			for i in self.post_processors:
				headers, response_body = i(self.request, headers, str(response_body))

			response_body = str(response_body)
			headers['Content-Length'] = str(len(response_body))

			# Deliver the goods
			start_response(status, headers.items())
			yield response_body
			logger.log_request(self.request, self.response, len(response_body))
			
	def _prep_start(self):
		'''
		Populate data gathered from global config.
		'''
		
		import preprocessors
		import postprocessors
		
		for i in config.pre_processors:
			self.pre_processors.append(getattr(preprocessors, i))
		
		for i in config.post_processors:
			self.post_processors.append(getattr(postprocessors, i))

		for mapping, path in config.static_map.items():
			logger.log_info("Mapping static directory: '%s' => '%s'" % (
				mapping, truncate(path, 40)))
			self.static_map[mapping] = path

	def start_fcgi(self, *args, **kwargs):
		'''
		Start the Flup FastCGI/WSGIServer interface. Any options passed to this method are
		automatically passed to the Flup WSGIServer.
		'''
		
		from flup.server.fcgi import WSGIServer
		
		self._prep_start()
		self.server_type = 'fcgi'
		logger.log_info("Starting FLUP WSGI Server...")
		WSGIServer(self, *args, **kwargs).run()

	def start_http(self, host='127.0.0.1', port=8080, *args, **kwargs):
		'''
		Start the Frame Development HTTPServer. Defaults to listen on localhost (port 8080).
		Note: Does not work on Windows unless ``auto_reload=False`` is passed, as currently
		the :mod:`frame.server.modulemonitor.ModuleMonitor` only works on *nix systems.
		
		Like :meth:`start_fcgi`, options are all passed to the HTTP Server. For additional
		parameters, please reference :mod:`frame.server.http.HTTPServer`.
		
		:param host: Listen host/address
		:param port: Listen port
		'''
		
		from frame.server.http import HTTPServer
		
		self.server_type = 'http'
		self._prep_start()
		logger.log_info("Starting Frame HTTP Server on %s:%s..." % (host, port))
		HTTPServer(self, host=host, port=port, *args, **kwargs).run()


app = App()
