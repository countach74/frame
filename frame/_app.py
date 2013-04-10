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
from threading import current_thread

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

import driverinterface


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
	
	def __init__(self, debug=True):
		'''
		Initialize the application with some sane defaults.
		'''
		
		self.static_map = StaticDispatcher(self)
		self.path = os.path.dirname(os.path.abspath(sys.argv[0]))
		self.routes = routes
		self.debug = debug

		# Jinja2 environment placeholder
		self.environment = None
		'''
		self.environment = Environment(loader=ChoiceLoader([
			FileSystemLoader(template_dir),
			PackageLoader('frame', 'templates')]))
		'''
		
		# Store data for each thread indiviually
		self.thread_data = {}

		self.toolset = toolset
		self.toolset.app = self
		
		self.drivers = self.setup_driver_database()
			
		# Setup partial views object
		self.partial_views = PartialViews(self)

		# Setup session interface
		#self.session_interface = sessions.SessionInterface(self)
		
		# Setup pre and post processor lists
		self.pre_processors = []
		self.post_processors = []

		# Setup ORM stuff
		forms.BasicForm._environment = self.environment
		orm.datatypes.CustomType._environment = self.environment
		self.orm_drivers = orm.available_drivers
		
		self.load_modules()
		
	def load_modules(self):
		import pkg_resources
		for entrypoint in pkg_resources.iter_entry_points('frame'):
			module = entrypoint.load()
			module(self)
		
	def setup_driver_database(self):
		drivers = driverinterface.DriverDatabase(self)
		
		drivers.add_interface(
			'session',
			driverinterface.SessionInterface,
			config=config.sessions)
			
		# Add postprocessor interface
		drivers.add_interface(
			'postprocessor',
			driverinterface.PostprocessorInterface)
			
		# Add preprocessor interface
		drivers.add_interface(
			'preprocessor',
			driverinterface.PreprocessorInterface)
		
		# Add routes interface
		drivers.add_interface(
			'dispatcher',
			driverinterface.DispatcherInterface,
			config=config.application)
		
		return drivers
		
	def _setup_thread(self):
		thread = current_thread()
		if thread not in self.thread_data:
			self.thread_data[thread] = {}
		
	@property
	def session(self):
		return self.thread_data[current_thread()]['session']
	
	@session.setter
	def session(self, value):
		self._setup_thread()
		self.thread_data[current_thread()]['session'] = value
		
	@session.deleter
	def session(self):
		del(self.thread_data[current_thread()]['session'])
		
	@property
	def request(self):
		return self.thread_data[current_thread()]['request']
		
	@request.setter
	def request(self, value):
		self._setup_thread()
		self.thread_data[current_thread()]['request'] = value
		
	@request.deleter
	def request(self):
		del(self.thread_data[current_thread()]['request'])
		
	@property
	def response(self):
		return self.thread_data[current_thread()]['response']
		
	@response.setter
	def response(self, value):
		self._setup_thread()
		self.thread_data[current_thread()]['response'] = value
		
	@response.deleter
	def response(self):
		del(self.thread_data[current_thread()]['response'])
		
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
			match, params = self.dispatcher.handle(environ=environ)

		# If TypeError or AttributeError occurs then no match was found; we should throw a 404.
		except (TypeError, AttributeError):
			return self.static_map.match(environ)
			
		# Any other errors are unexpected
		except Exception, e:
			raise Error500

		# Otherwise, we should be good to handle the request
		else:
			for key, value in params.items():
				if key in ('controller', 'action', 'method'):
					del(params[key])
					
			# Process hook entry points
			for hook in config.hooks:
				try:
					hook.enter(match.im_self)
				except Exception, e:
					raise Error500
				
			# Process hook exit points
			def exit_hooks():
				for hook in config.hooks:
					try:
						hook.exit(match.im_self)
					except Exception, e:
						raise Error500

			response = Response(self, match, params)
			
			try:
				self.session = self.drivers.session.get_session()
			except Exception, e:
				exit_hooks()
				raise Error500

			self.environment.globals['session'] = self.session
			self.environment.globals['tools'] = toolset

			for i in self.pre_processors:
				try:
					i(self.request, response)
				except Exception, e:
					raise Error500
				
			def save_session():
				try:
					self.drivers.session.save_session(self.session)
				except Exception, e:
					exit_hooks()
					raise Error500

			try:
				response.render()
			except HTTPError, e:
				exit_hooks()
				save_session()
				raise e
			except Exception, e:
				exit_hooks()
				raise Error500
			
			# Run exit hooks
			exit_hooks()
			
			# Save the session before yielding the response
			save_session()

		return response

	def __call__(self, environ, start_response):
		'''
		A callable to allow WSGI compliance.
		
		:param environ: WSGI environment
		:param start_response: The start_response function passed by the WSGI server
		:yield: Response body
		'''
		
		try:
			response = self._dispatch(environ)
		except HTTPError, e:
			e.render(self)
			response = e.response

		# Need to do something more elegant to handle generators/chunked encoding...
		# Also need to come up with a better way to log chunked encodings
		if type(response.body) is types.GeneratorType:
			start_response(response.status, response.headers.items())
			response_length = 0
			for i in response.body:
				yield str(i)
				response_length += len(i)
			logger.log_request(self.request, response, response_length)

		else:
			# Apply post processors
			for i in self.post_processors:
				i(self.request, response)

			#response_body = str(response_body)
			#headers['Content-Length'] = str(len(response_body))

			# Deliver the goods
			start_response(response.status, response.headers.items())
			yield str(response.body)
			logger.log_request(self.request, response, len(response.body))
			
		self._remove_thread_data()
		
	def _remove_thread_data(self):
		thread = current_thread()
		if thread in self.thread_data:
			del(self.thread_data[thread])
		if thread in self.routes.thread_data:
			del(self.routes.thread_data[thread])
			
	def _prep_start(self):
		'''
		Populate data gathered from global config.
		'''
		
		for i in config.pre_processors:
			self.pre_processors.append(self.drivers.preprocessor[i])
		
		for i in config.post_processors:
			self.post_processors.append(self.drivers.postprocessor[i])

		for mapping, path in config.static_map.items():
			logger.log_info("Mapping static directory: '%s' => '%s'" % (
				mapping, truncate(path, 40)))
			self.static_map[mapping] = path
			
		# Setup Jinja2 Environment
		loaders = list(config.templates.loaders)
		loaders.insert(0, FileSystemLoader(config.templates.directory))
		self.environment = Environment(loader=ChoiceLoader(loaders))
		self.environment.globals.update(config.templates.globals)
		self.environment.filters.update(config.templates.filters)
		
		# Initialize dispatcher
		#self.dispatcher = load_driver('dispatcher', config.application.dispatcher)(self)
		self.dispatcher = self.drivers.dispatcher.current(self)
		
			
	def daemonize(self, host='127.0.0.1', port=8080, ports=None, server_type='fcgi', *args, **kwargs):
		from daemonize import daemonize
		
		daemonize(self, host, port, ports, server_type, *args, **kwargs)

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
