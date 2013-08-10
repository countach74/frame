class DriverInterface(dict):
	'''
	A glorified dictionary to store the drivers. Provides some hooks to customize how the
	various drivers should be instantiated and used.
	'''
	def __init__(self, database, drivers={}, config=None):
		'''
		Initialize.
		
		:param database: The :class:`DriverDatabase`
		:param drivers: Any drivers that should be added immediately
		:param config: A config directive to use; optional
		'''
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
		
	def load_driver(self, name, *args, **kwargs):
		'''
		Loads the specified driver (calls :meth:`init`).
		
		:param name: The name of the driver to load
		:return: An instantiated driver
		'''
		return self.init(self[name], *args, **kwargs)
		
	def add_driver(self, name, driver):
		'''
		Adds a driver to the interface. This is what :meth:`DriverDatabase.register` calls
		indirectly. There really isn't a need to use this directly and you probably
		shouldn't (it may end up being deprecated).
		
		:param name: What to call the driver
		:param driver: The driver
		'''
		self[name] = driver
		
	def init(self, driver, *args, **kwargs):
		'''
		A hook to instruct the interface how to instantiate the driver.
		
		The default simply returns the interface called with no arguments. If a driver
		requires more information than this on instantiation, you could do something like
		this::
		
			def init(self, driver):
				return driver(frame.app, 'hello world')
				
		... or whatever.
		
		:param driver: The driver to instantiate
		:return: An instantiated driver
		'''
		return driver(*args, **kwargs)
		
	def load_current(self, *args, **kwargs):
		'''
		Attempts to guess the currently loaded driver, if a config directive was given and
		has a 'driver' key.
		'''
		if self.config and 'driver' in self.config:
			return self.load_driver(self.config.driver, *args, **kwargs)
		else:
			raise AttributeError("No driver config specified or config lacks 'driver' item")
		
	@property
	def current(self):
		'''
		Like :meth:`load_current` only doesn't instantiate the driver.
		'''
		if self.config and 'driver' in self.config:
			return self[self.config.driver]
		else:
			raise AttributeError("No driver config specified or config lacks 'driver' item")
