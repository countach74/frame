import pickle
from _dotdict import DotDict
from errors import SessionLoadError, SessionSaveError
import datetime
from uuid import uuid4
from _config import config


class Session(object):
	import random

	def __init__(self, app, interface, force=False):
		self._app = app
		self.interface = interface

		# Set default modified value to False
		self.modified = False
		
		# Create session cookie if it does not already exist
		key_name = config['sessions.cookie_name']
		expires = config['sessions.expires']

		self.init()

		if key_name in app.request.cookies and not force:
			self._key = app.request.cookies[key_name]
			self._data = self.load(self._key)
		else:
			self._key = self.make_session_key()
			self._data = {}
			app.response.set_cookie(key_name, self._key, expires=expires)
			self.modified = True

	def __getitem__(self, key):
		return self._data[key]

	def __setitem__(self, key, value):
		self.modified = True
		self._data[key] = value

	def __contains__(self, key):
		return key in self._data

	def _save(self, key, data):
		if self.modified:
			self.save(key, data)
			self.cleanup_sessions()

	def init(self):
		pass

	def get_expiration(self):
		now = datetime.datetime.utcnow()
		delta = datetime.timedelta(hours=config['sessions.expires'])
		return now + delta

	@classmethod
	def make_session_key(self, length=128,
		characters='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):

		num_chars = len(characters)
		possibilities = pow(num_chars, length)
		choice = self.random.randint(0, possibilities - 1)
		key = []

		for i in xrange(length):
			ch = choice % num_chars
			key.append(characters[ch])
			choice = choice / num_chars

		return ''.join(key)

	def cleanup_sessions(self):
		pass

	def remove(self):
		self.expire(self._key)


class MemorySession(Session):
	sessions = {}
	last_cleanup = datetime.datetime.utcnow()

	def load(self, key):
		try:
			return self.sessions[key]['data']
		except KeyError:
			raise SessionLoadError

	def save(self, key, data):
		try:
			self.sessions[key]['data'] = data
		except KeyError:
			self.sessions[key] = {'data': data, 'expiration': self.get_expiration()}

	def cleanup_sessions(self):
		now = datetime.datetime.utcnow()
		threshold = self.last_cleanup + datetime.timedelta(minutes=config['sessions.memory.cleanup_frequency'])
		if now > threshold:
			for k, v in self.sessions.items():
				if now > v['expiration']:
					del(self.sessions[k])

	def expire(self, key):
		if key in self.sessions:
			del(self.sessions[key])


class MemcacheSession(Session):
	import memcache
	import time
	prefix = 'FRAME_SESSION::'

	def init(self):
		import memcache

		if not hasattr(self.interface, 'memcache'):
			self.interface.memcache = self.memcache.Client(['127.0.0.1:11211'])

		self.db = self.interface.memcache

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
		expiration = self.time.mktime(self.get_expiration().timetuple())
		self.db.set(self.prefix + key, pickle.dumps(data), time=expiration)


class SessionInterface(object):
	def __init__(self, app, **kwargs):
		self.app = app

	@property
	def backend(self):
		return globals()[config['sessions.backend'] + 'Session']

	def get_session(self):
		try:
			return self.backend(self.app, self)
		except SessionLoadError:
			return self.backend(self.app, self, force=True)

	def save_session(self, session):
		session._save(session._key, session._data)
