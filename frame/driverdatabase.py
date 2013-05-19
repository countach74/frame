'''
The driver interface is a globally-used interface for providing various drivers to the
Frame application. The :class:`DriverDatabase` is instantiated at app.drivers and
contains a collection of :class:`DriverInterfaces` objects that instruct Frame how
to interact with the various drivers. Access to a particular driver is done via dot
notation, like so::

	frame.app.drivers.session.memory
	
The above will access the :class:`frame.sessions.MemorySession` class, as it is by
default registered to the 'session' driver interface under the name 'memory'.


Manually Registering Drivers
============================

Drivers can be registered easily via ``frame.app.drivers``. Consider the following
example::

	import frame
	
	def dummy_postprocessor(request, response):
		print 'hello, world!'
	
	frame.app.drivers.register('postprocessor', 'dummy', dummy_postprocessor)
	
This exposes the ``dummy_postprocessor`` to the ``postprocessor`` driver interface using
the name ``dummy``. To access the driver, you could now do::

	frame.app.drivers.postprocessor.dummy
	
*Note: Post processors are not enabled by default; you must append 'dummy' to the
postprocessor config directive (``frame.config.postprocessors``) for it to be activated.*
'''

from errors import SessionLoadError
from _config import config

# Import base drivers
from postprocessors import (deflate, handle_head_request, add_last_modified, jsonify,
	add_date)
from preprocessors import (form_url_decoder, form_json_decoder, form_multipart_decoder,
	handle_query_string)
from dispatchers import RoutesDispatcher
#import _logger as logger

# Import Singleton so that we can make DriverDatabase a Singleton :)
from util import Singleton

from driverinterface import DriverInterface
			

class DriverDatabase(Singleton):
	'''
	A very simple class to keep track of the various registered driver interfaces. Please
	note that this is definitively *not* related to a real database. I just couldn't think
	of a better name for it.
	'''
	def __init__(self, app):
		'''
		Initialize.
		
		:param app: The Frame application
		'''
		self.app = app
		self.interfaces = {}
		
	def add_interface(self, interface_name, interface, drivers={}, config=None):
		'''
		Add a DriverInterface to the DriverDatabase.
		
		For example, ``frame.app`` adds the SessionInterface via something kind of like
		this::
		
			self.drivers.add_interface('session', SessionInterface)
		
		:param interface_name: What to name the interface
		:param interface: The DriverInterface to use
		:param drivers: A dictionary of drivers to register with the driver interface upon
			adding it to the driver 'database'
		:param config: A config directive to pass to the interface upon instantiation
		'''
		self.interfaces[interface_name] = interface(self, drivers, config)
		
	def register(self, interface_name, driver_name, driver):
		'''
		Register a driver to a specified driver interface.
		
		:param interface_name: The name of the interface to register the driver with
		:param driver_name: What to call the driver
		:param driver: The driver. :)
		'''
		self.interfaces[interface_name].add_driver(driver_name, driver)
		
	def __getattr__(self, key):
		try:
			return self.interfaces[key]
		except KeyError:
			raise AttributeError(key)
		
	def __repr__(self):
		return "<DriverDatabase(%s)>" % ', '.join(self.interfaces.keys())
		
	
class PostprocessorInterface(DriverInterface):
	def __init__(self, *args, **kwargs):
		DriverInterface.__init__(self, *args, **kwargs)
		
		self.update({
			'deflate': deflate,
			'handle_head_request': handle_head_request,
			'add_last_modified': add_last_modified,
			'add_date': add_date,
			'jsonify': jsonify
		})
	
class PreprocessorInterface(DriverInterface):
	def __init__(self, *args, **kwargs):
		DriverInterface.__init__(self, *args, **kwargs)
		
		self.update({
			'form_url_decoder': form_url_decoder,
			'form_json_decoder': form_json_decoder,
			'form_multipart_decoder': form_multipart_decoder,
			'handle_query_string': handle_query_string
		})
		
		
class DispatcherInterface(DriverInterface):
	def __init__(self, *args, **kwargs):
		DriverInterface.__init__(self, *args, **kwargs)
		
		self.update({
			'routes': RoutesDispatcher
		})
		
	@property
	def current(self):
		return self[self.config.dispatcher]
		
		
class LogInterface(DriverInterface):
	def __init__(self, *args, **kwargs):
		DriverInterface.__init__(self, *args, **kwargs)
		
		self.logger = None
		
		self.update({
			'stdout': logger.StdoutLogger,
			'null': logger.NullLogger,
			'production': logger.ProductionLogger
		})
		
		logger.logger = self
		
	def __getattr__(self, key):
		if key.startswith('log_'):
			return getattr(self.logger, key)
		else:
			return object.__getattr__(self, key)
		
	def init(self, driver):
		if not self.logger:
			options = self.config[self.config.driver]
			self.logger = driver(**options)
		return self.logger
