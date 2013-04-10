from sessions import MemcacheSession, MemorySession, FileSession, MysqlSession
from errors import SessionLoadError
from _config import config


class DriverInterface(object):
	def __init__(self, database, drivers={}, config=None):
		self.database = database
		self.drivers = drivers
		self.config = config
		
	def load_driver(self, name):
		return self.init(self.drivers[name])
		
	def add_driver(self, name, driver):
		self.drivers[name] = driver
			
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


class SessionInterface(DriverInterface):
	def init(self, driver):
		try:
			return driver(self.database.app, self)
		except SessionLoadError:
			return driver(self.database.app, self, force=True)
			
	def get_session(self):
		return self.current
		
	def save_session(self, session):
		session._save(session._key, session._data)