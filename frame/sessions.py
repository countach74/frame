import pickle
from _dotdict import DotDict
from uuid import uuid4
from errors import SessionLoadError, SessionSaveError


class Session(object):
	def __init__(self, app, interface, force=False):
		self._app = app
		self._interface = interface
		
		# Create session cookie if it does not already exist
		key_name = app.config.sessions.key_name
		expires = app.config.sessions.expires

		if key_name in app.request.cookies and not force:
			self._key = app.request.cookies[key_name]
			self._data = self.load(self._key)
		else:
			self._key = str(uuid4())
			self._data = {}
			app.response.set_cookie(key_name, self._key, expires=expires)

		self.init()

	def __getitem__(self, key):
		return self._data[key]

	def __setitem__(self, key, value):
		self._data[key] = value

	def __contains__(self, key):
		return key in self._data

	def init(self):
		pass

	def load(self, key):
		pass

	def save(self, key, data):
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


class SessionInterface(object):
	def __init__(self, app, session_type='MemorySession', **kwargs):
		self.app = app
		self.session_type = globals()[session_type]
		self.config = DotDict(kwargs)

	def get_session(self):
		try:
			return self.session_type(self.app, self)
		except SessionLoadError:
			key_name = self.app.config.sessions.key_name
			self.app.response.delete_cookie(key_name)
			return self.session_type(self.app, self, True)

	def save_session(self, session):
		try:
			session.save(session._key, session._data)
		except SessionSaveError:
			print "COULD NOT SAVE SESSION!"
