import pickle
from _dotdict import DotDict
from uuid import uuid4
from errors import SessionLoadError, SessionSaveError


class Session(object):
	def __init__(self, app, interface, force=False):
		self._app = app
		self.interface = interface
		
		# Create session cookie if it does not already exist
		key_name = app.config.sessions.key_name
		expires = app.config.sessions.expires

		self.init()

		if key_name in app.request.cookies and not force:
			self._key = app.request.cookies[key_name]
			self._data = self.load(self._key)
		else:
			self._key = str(uuid4())
			self._data = {}
			app.response.set_cookie(key_name, self._key, expires=expires)

	def __getitem__(self, key):
		return self._data[key]

	def __setitem__(self, key, value):
		self._data[key] = value

	def __contains__(self, key):
		return key in self._data

	def init(self):
		pass


class MemorySession(Session):
	sessions = {}

	def load(self, key):
		try:
			return self.sessions[key]
		except KeyError:
			raise SessionLoadError

	def save(self, key, data):
		self.sessions[key] = data


class MemcacheSession(Session):
	prefix = 'FRAME_SESSION::'

	def init(self):
		import memcache

		if 'servers' not in self.interface.config:
			self.interface.config.servers = ['127.0.0.1:11211']

		self.interface.config._memcache = memcache.Client(self.interface.config.servers)
		self.db = self.interface.config._memcache

	def load(self, key):
		import pickle

		raw_data = self.db.get(self.prefix + key)
		if raw_data:
			try:
				return pickle.loads(raw_data)
			except IndexError:
				raise SessionLoadError
		else:
			raise SessionLoadError

	def save(self, key, data):
		self.db.set(self.prefix + key, pickle.dumps(data))


class SessionInterface(object):
	def __init__(self, app, backend='Memory', **kwargs):
		self.app = app
		self._backend = globals()[backend + 'Session']
		self.config = DotDict(kwargs)

	@property
	def backend(self):
		return self._backend

	@backend.setter
	def backend(self, value):
		self._backend = globals()[value + 'Session']

	def get_session(self):
		try:
			return self.backend(self.app, self)
		except SessionLoadError:
			return self.backend(self.app, self, force=True)

	def save_session(self, session):
		session.save(session._key, session._data)
