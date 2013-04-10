from errors import SessionLoadError
from _config import config

# Import base drivers
from sessions import MemcacheSession, MemorySession, FileSession, MysqlSession
from postprocessors import deflate, handle_head_request, add_last_modified, jsonify
from preprocessors import (form_url_decoder, form_json_decoder, form_multipart_decoder,
	handle_query_string)
from dispatchers import RoutesDispatcher


class DriverInterface(dict):
	def __init__(self, database, drivers={}, config=None):
		self.database = database
		self.config = config
		
		dict.__init__(self, drivers)
		
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(key)
		
	def __repr__(self):
		return "<DriverInterface(%s)>" % ', '.join(self.keys())
		
	def load_driver(self, name):
		return self.init(self[name])
		
	def add_driver(self, name, driver):
		self[name] = driver
		
	def init(self, driver):
		return driver()
		
	@property
	def current(self):
		if self.config:
			return self.load_driver(self.config.driver)
		else:
			raise AttributeError("No driver config specified")
			

class DriverDatabase(object):
	def __init__(self, app):
		self.app = app
		self.interfaces = {}
		
	def add_interface(self, interface_name, interface, drivers={}, config=None):
		self.interfaces[interface_name] = interface(self, drivers, config)
		
	def register_driver(self, interface_name, driver_name, driver):
		self.interfaces[interface_name].add_driver(driver_name, driver)
		
	def __getattr__(self, key):
		try:
			return self.interfaces[key]
		except KeyError:
			raise AttributeError(key)
		
	def __repr__(self):
		return "<DriverDatabase(%s)>" % ', '.join(self.interfaces.keys())


class SessionInterface(DriverInterface):
	def __init__(self, *args, **kwargs):
		DriverInterface.__init__(self, *args, **kwargs)
		
		self.update({
			'memcache': MemcacheSession,
			'memory': MemorySession,
			'file': FileSession,
			'mysql': MysqlSession
		})
		
	def init(self, driver):
		try:
			return driver(self.database.app, self)
		except SessionLoadError:
			return driver(self.database.app, self, force=True)
			
	def get_session(self):
		return self.current
		
	def save_session(self, session):
		session._save(session._key, session._data)
		
	
class PostprocessorInterface(DriverInterface):
	def __init__(self, *args, **kwargs):
		DriverInterface.__init__(self, *args, **kwargs)
		
		self.update({
			'deflate': deflate,
			'handle_head_request': handle_head_request,
			'add_last_modified': add_last_modified,
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