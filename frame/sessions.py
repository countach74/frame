import pickle
from dotdict import DotDict
from errors import SessionLoadError, SessionSaveError
import datetime
from uuid import uuid4
from _config import config
import os
from threading import RLock
from _logger import logger


class Session(object):
	import random

	def __init__(self, app, interface, force=False):
		self._app = app
		self.interface = interface

		# Create session cookie if it does not already exist
		key_name = config.sessions.cookie_name
		expires = config.sessions.expires

		self.init()

		if key_name in app.request.cookies and not force:
			self._key = app.request.cookies[key_name]
			self._data = self.load(self._key)
		else:
			self._key = self.make_session_key()
			self._data = {}
			app.response.set_cookie(key_name, self._key, expires=expires)

	def __getitem__(self, key):
		return self._data[key]

	def __setitem__(self, key, value):
		self._data[key] = value

	def __contains__(self, key):
		return key in self._data
		
	def __repr__(self):
		return "<Session(%s, %s)>" % (self._key, self._data)
		
	def __str__(self):
		return str(self._data)

	def _save(self, key, data):
		self.save(key, data)
		self.cleanup_sessions()

	def init(self):
		pass

	def get_expiration(self):
		now = datetime.datetime.utcnow()
		delta = datetime.timedelta(hours=config.sessions.expires)
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
		self._data = {}
		
	def commit(self):
		self._save(self._key, self._data)
		
		
class MysqlSession(Session):
	__last_cleanup = datetime.datetime.utcnow()
	__lock = RLock()
	
	try:
		import MySQLdb as __mysql
	except ImportError:
		raise ImportError("Could not use mysql session backend: MySQLdb module not found.")
	
	@property
	def __connection(self):
		return config.sessions.mysql.connection
		
	@__connection.setter
	def __connection(self, value):
		config.sessions.mysql.connection = value
			
	def __init__(self, *args, **kwargs):
		if not self.__connection:
			settings = config.sessions.mysql
			
			required_fields = (
				'database',
				'user',
				'password',
				'table'
			)
			
			if any((not settings[i] for i in required_fields)):
				raise StandardError("Could not setup MySQL connection. The following configuration "
					"options must be set: %s" % ', '.join(required_fields))
			else:
				self.__connection = self.__mysql.Connection(
					host=settings['host'],
					port=settings['port'],
					user=settings['user'],
					passwd=settings['password'],
					db=settings['database']
				)
				
		Session.__init__(self, *args, **kwargs)
				
	def load(self, key):
		self.__lock.acquire()
		table = config.sessions.mysql.table
		cursor = self.__connection.cursor()
		
		cursor.execute("select data from %s where session_id=%%s limit 1" % table, key)
		result = cursor.fetchone()
		
		self.__lock.release()
		if result:
			return pickle.loads(result[0])
			
		else:
			raise SessionLoadError
		
	def save(self, key, data):
		self.__lock.acquire()
		table = config.sessions.mysql.table
		cursor = self.__connection.cursor()
		expiration = self.get_expiration()
		pickled_data = pickle.dumps(data)
		
		cursor.execute(
			"replace into %s(session_id, expiration, data) values(%%s, %%s, %%s)" % table,
			(key, expiration, pickled_data))
			
		self.__connection.commit()
		self.__lock.release()
			
	def expire(self, key):
		self.__lock.acquire()
		cursor = self.__connection.cursor()
		table = config.sessions.mysql.table
		
		cursor.execute("delete from %s where session_id = %%s" % table,
			key)
			
		self.__connection.commit()
		self.__lock.release()
			
	def cleanup_sessions(self):
		now = datetime.datetime.now()
		threshold = self.__last_cleanup + datetime.timedelta(minutes=config.sessions.cleanup_frequency)
		
		if now > threshold:
			self.__lock.acquire()
			self.__last_cleanup = datetime.datetime.utcnow()
			table = config.sessions.mysql.table
			cursor = self.__connection.cursor()
			now = datetime.datetime.now()
		
			cursor.execute("delete from %s where expiration >= %%s" % table, now)
			
			self.__connection.commit()
			self.__lock.release()
		
		
class FileSession(Session):
	__lock = RLock()
	last_cleanup = datetime.datetime.utcnow()
	
	def get_path(self, key):
		return os.path.join(config.sessions.file.directory, key)
	
	def load(self, key):
		self.__lock.acquire()
		path = self.get_path(key)
		
		def load_session(f):
			session = pickle.load(f)
			return session['data']
		
		try:
			with open(path, 'r') as f:
				result = load_session(f)
				self.__lock.release()
				return result
		except EnvironmentError:
			self.__lock.release()
			raise SessionLoadError
		except Exception, e:
			self.__lock.release()
			raise e
		
	def save(self, key, data):
		self.__lock.acquire()
		path = self.get_path(key)
		
		def save_session(f):
			session = {
				'data': data,
				'expiration': self.get_expiration()
			}
			
			pickle.dump(session, f)
			
		try:
			with open(path, 'w') as f:
				save_session(f)
		except IOError:
			self.__lock.release()
			raise SessionSaveError
		except Exception, e:
			self.__lock.release()
			raise e
			
		self.__lock.release()
		
	def cleanup_sessions(self):
		session_path = config.sessions.file.directory
		now = datetime.datetime.utcnow()
		threshold = FileSession.last_cleanup + datetime.timedelta(
			minutes=config.sessions.cleanup_frequency)
			
		if now > threshold:
			FileSession.last_cleanup = datetime.datetime.utcnow()
			logger.log_info("Starting session cleanup...")
			for dirpath, dirnames, filenames in os.walk(session_path):
				for i in filenames:
					path = os.path.join(dirpath, i)
				
					self.__lock.acquire()
					try:
						with open(path, 'r+') as f:
							session_data = pickle.load(f)
	
						if now > session_data['expiration']:
							try:
								os.remove(path)
							except IOError:
								self.__lock.release()
								logger.log_warning("Could not remove session file '%s'" % path)
							except Exception, e:
									self.__lock.release()
									raise e
					except Exception, e:
						self.__lock.release()
						raise e
					else:
						self.__lock.release()
			logger.log_info("Session cleanup complete")
		
	def expire(self, key):
		self.__lock.acquire()
		path = self.get_path(key)
		try:
			os.remove(path)
		except IOError:
			self.__lock.release()
			logger.log_warning("Could not remove session file '%s'" % path)


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
		threshold = MemorySession.last_cleanup + datetime.timedelta(
			minutes=config.sessions.cleanup_frequency)
			
		if now > threshold:
			logger.log_info("Starting session cleanup...")
			MemorySession.last_cleanup = datetime.datetime.utcnow()
			for k, v in self.sessions.items():
				if now > v['expiration']:
					del(self.sessions[k])
			logger.log_info("Session cleanup complete")

	def expire(self, key):
		if key in self.sessions:
			del(self.sessions[key])


class MemcacheSession(Session):
	import memcache
	import time
	prefix = 'FRAME_SESSION::'

	def init(self):
		import memcache

		if not self.db:
			self.db = self.memcache.Client(['127.0.0.1:11211'])

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
	
	@property
	def db(self):
		return config.sessions.memcache.connection
		
	@db.setter
	def db(self, value):
		config.sessions.memcache.connection = value

	def save(self, key, data):
		expiration = self.time.mktime(self.get_expiration().timetuple())
		self.db.set(self.prefix + key, pickle.dumps(data), time=expiration)
		
	def expire(self, key):
		self.db.set(self.prefix + key, '', time=-1)


class SessionInterface(object):
	def __init__(self, app, **kwargs):
		self.app = app

	@property
	def backend(self):
		return globals()[config.sessions.driver.title() + 'Session']

	def get_session(self):
		try:
			return self.backend(self.app, self)
		except SessionLoadError:
			return self.backend(self.app, self, force=True)

	def save_session(self, session):
		session._save(session._key, session._data)
