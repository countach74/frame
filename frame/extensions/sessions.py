'''
Frame allows for a variety of session backend storages. In fact, you can use pretty
much anything you can dream up to store session data; if it's not here already, make
it yourself--it's easy! If you are interested in creating your own session driver(s),
please see :ref:`create_session_driver`.
'''


import pickle
from ..dotdict import DotDict
from ..errors import SessionLoadError, SessionSaveError, Error500
import datetime
from uuid import uuid4
from .._config import config
import os
from .._logger import logger
from ..driverinterface import DriverInterface
from threading import RLock
from ..util import Hook


sessions_config = DotDict({
  'driver': 'memory',
  'cookie_name': 'FrameSession',
  'expires': 168,
  'cleanup_frequency': 30,
  
  'memcache': {
    'prefix': 'FRAME_SESSION::',
    'connection': None,
    'servers': ['127.0.0.1:11211'],
  },

  'memory': {},

  'file': {
    'directory': 'sessions',
  },

  'mysql': {
    'host': 'localhost',
    'port': 3306,
    'connection': None,
    'database': None,
    'table': 'frame_sessions',
    'user': None,
    'password': None,
  },
})


class Session(object):
  '''
  The :class:`Session` class is the basic session interface that all session drivers
  implement. In order for a driver to work, at a minimum, the :meth:`save` and
  :meth:`load` methods must be implemented. In some cases, this may be adequate but more
  than likely, you will want to also implement :meth:`expires` and
  :meth:`cleanup_sessions`.
  
  Frame sessions are loaded at the beginning of a request and saved at the end of a
  request. Drivers do not have to save session data each time it changes, but only once
  at the end of the request and then it must save the entire dataset.
  
  *Note:* The session's data is stored at :attr:`_data`.
  '''
  
  import random

  def __init__(self, app, interface, force=False):
    '''
    Initializes the session. This should not be overridden. Instead, if you need a hook
    into the session initialization, implement :meth:`init`.
    
    :param app: The Frame application
    :param interface: The :class:`SessionInterface` that created the session
    :param force: A boolean that specifies whether or not session creation should be
      forced. Necessary when a client passes a session token that no longer exists
      in the backend session storage
    '''
    
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
    
  def __delitem__(self, key):
    del(self._data[key])

  def __contains__(self, key):
    return key in self._data
    
  def __repr__(self):
    return "<Session(%s, %s)>" % (self._key, self._data)
    
  def __str__(self):
    return str(self._data)

  def _save(self, key, data):
    self.save(key, data)
    self.cleanup_sessions()

  def update(self, data):
    self._data.update(data)

  def init(self):
    '''
    A hook that is called at session initialization. Use this if you need to perform any
    operation on initialization. It is called after the Frame app and
    :class:`SessionInterface` are saved to the session, but before any data is saved
    or loaded.
    '''
    pass

  def get_expiration(self):
    '''
    Returns a datetime object set to utcnow() + however many hours sessions are
    configured to last (as specified at ``config.sessions.expires``).
    
    :return: Datetime object
    '''
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
    '''
    Use to cleanup sessions.
    
    **NOTE**: This is called *every time a session is saved*. In order to not destroy
    performance, the session driver must do a check to discover if it's really time to
    run a session cleanup. Hopefully in the future, we will make this more elegant.
    '''
    pass

  def remove(self):
    '''
    Calls the session's :meth:`expire` method and resets the stored data to an empty
    dictionary.
    '''
    self.expire(self._key)
    self._data = {}
    
  def commit(self):
    '''
    Force the session to save data, rather than wait for the end of request.
    '''
    self._save(self._key, self._data)
    
  def load(self, key):
    '''
    Fetch the session data for the requested key and return it as a dictionary. If the
    key cannot be found, throw :exc:`frame.errors.SessionLoadError`. It is very
    important that this exception is thrown if the key is not found. Do not leave
    it out! :)
    
    :param key: A unique session key
    :return: Session data as a dictionary
    '''
    pass
  
  def save(self, key, data):
    '''
    Save the session data with the given key. If the session cannot be saved, throw
    :exc:`frame.errors.SessionSaveError`. Actually, throwing this error is not that
    important (unlike throwing :exc:`frame.errors.SessionLoadError` in the
    :meth:`load` method).
    
    :param key: A unique session key
    :param data: The session data as a dictionary
    '''
    pass
    
    
class MysqlSession(Session):
  __last_cleanup = datetime.datetime.utcnow()
  __lock = RLock()
  
  @property
  def __connection(self):
    return config.sessions.mysql.connection
    
  @__connection.setter
  def __connection(self, value):
    config.sessions.mysql.connection = value
      
  def __init__(self, *args, **kwargs):
    try:
      import MySQLdb as __mysql
    except ImportError:
      raise ImportError("Could not use mysql session backend: MySQLdb module not found.")
    
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
        self.__connection = __mysql.Connection(
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
  import time
  prefix = 'FRAME_SESSION::'
  
  def init(self):
    try:
      import memcache
    except ImportError:
      raise ImportError("Memcache sessions unavailable; cannot find 'memcache' module")

    if not self.db:
      self.db = memcache.Client(['127.0.0.1:11211'])

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
    
    
class SessionHook(Hook):
  def __init__(self, app, controller):
    self.app = app
    self.controller = controller
    
  def __enter__(self):
    try:
      self.app.session = self.app.drivers.session.get_session()
      self.controller.session = self.app.session
    except Exception, e:
      raise Error500
    
    if self.app.drivers.template:
      self.app.drivers.template.globals['session'] = self.app.session
    
  def __exit__(self, e_type, e_value, e_tb):
    self.app.drivers.session.save_session(self.app.session)
    
  
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
      
  # Alias to match old session interface
  get_session = DriverInterface.load_current
    
  def save_session(self, session):
    session._save(session._key, session._data)


def register_config(conf):
  conf.sessions = sessions_config
  conf.hooks.append('session')


def register_driver(drivers):
  drivers.register('hook', 'session', SessionHook)

  drivers.add_interface(
    'session',
    SessionInterface,
    config=sessions_config)

  app = drivers.app
  App = app.__class__

  def get_session(self):
    return app.thread_data['session']

  def set_session(self, value):
    app.thread_data['session'] = value

  def del_session(self):
    del(self.thread_data['session'])

  App.session = property(get_session, set_session, del_session)
