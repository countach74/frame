'''
Some simple utilities to help out with everyday operations. Some of these
are used internally by Frame; some are designed to be used by web developers.
'''


import re
import types
from threading import RLock
import time
import datetime
import json
from _config import config


class Decorator(object):
  '''
  Simple mixin to aid in making decorators.
  '''
  
  def __get__(self, instance, parent=None):
    return types.MethodType(self, instance)
    
    
class Authorization(Decorator):
  '''
  Simple class to facilitate access control. Designed to be subclassed; not
  complete by itself, this is really more of a mixin.
  
  Here is a simple example::
  
    class Auth(Authorization):
      def authorize(self, f, *args, **kwargs):
        if 'user' in frame.app.session and any((i in self.groups for i in user_groups)):
          # Allow access
          return f(*args, **kwargs)
          
        else:
          # Deny access
          frame.app.current_controller.redirect('/login')
          
          
  Now, to use our Auth class, we just decorate a controller method with it, like so::
  
    class Admin(frame.Controller):
      @Auth(groups=['admin', 'dev'])   # Only let 'admin' and 'dev' users through
      def index(self):
        return 'admin area'
  '''
  
  def __init__(self, groups=[], users=[]):
    self.groups = groups
    self.users = users
    
  def __call__(self, f):
    def auth(*args, **kwargs):
      return self.authorize(f, *args, **kwargs)
      
    # Fix the auto-template routing issue w/decorators
    auth.__name__ = f.__name__
    
    return auth
    
  def authorize(self, f, *args, **kwargs):
    '''
    Override this method to do authorization checks and return the appropriate
    data, depending on user/group access permissions.
    '''
    pass


def parse_query_string(string):
  from cgi import parse_qs

  data = parse_qs(string, True)
  for key, value in data.items():
    if len(value) == 1:
      data[key] = value[0]

  return data


def import_all_modules(origin_file):
  import os
  import glob

  # Get the directory that the file is from
  path = os.path.dirname(os.path.abspath(origin_file))

  old_path = os.getcwd()

  # Chdir to the directory
  os.chdir(path)

  # Find all Python modules within the directory
  module_paths = glob.glob("%s/*.py" % path)
  module_files = map(os.path.basename, module_paths)

  modules = []

  for module, extension in map(os.path.splitext, module_files):
    if not module.startswith('__'):
      __import__(module)

  # Chdir back to original directory
  os.chdir(old_path)
  
  
def make_resource(controller, path):
  template_dir = re.sub("(/{.*?})", '', path).lstrip('/')
  
  controller.__resource__ = {
    'base_uri': path,
    'template_dir': template_dir
  }


def truncate(text, length=30):
  '''
  Truncate text. Really long text becomes::
  
    This is...long text
    
  :param text: String to truncate
  :param length: Maximum length to allow before truncating
  :return: Truncated string
  '''
  if len(text) > length:
    first_half = text[0:length/2]
    second_half = text[-length/2:]
    return "%s...%s" % (first_half, second_half)
  else:
    return text


class FileLogger(object):
  '''
  A thread-safe file logging tool. This is intended to be used as a target
  for the stdout logger. It can be configured like so::
  
    frame.config.logger.stdout.out = FileLogger('/tmp/framelog.out')
    frame.config.logger.stdout.err = FileLogger('/tmp/framelog.err')
    
  `Caution`: Make sure that the application user has appropriate permissions
    to write to the file. Since you're redirecting logging output, any trouble
    that is encountered may not be reported and logging won't work, so you
    can end up in the dark.
  '''
  
  def __init__(self, path):
    '''
    Initialize the FileLogger
    
    :param path: The file to log to. Must have write access to this file!
    '''
    self.path = path
    self.lock = RLock()
    
    try:
      with open(path, 'a') as f:
        pass
    except EnvironmentError, e:
      raise e.__class__("%s does not appear to be writable." % path)
    
  def write(self, data):
    self.lock.acquire()
    try:
      with open(self.path, 'a') as f:
        f.write(data)
    finally:
      self.lock.release()
      
      
class Singleton(object):
  """
  A simple mixin to make a class behave like a Singleton.
  """
  __instance = None
  
  def __new__(cls, *args, **kwargs):
    if not cls.__instance:
      cls.__instance = object.__new__(cls, *args, **kwargs)
    
    return cls.__instance
    
  @classmethod
  def _clear_instance(self):
    del(self.__instance)
    self.__instance = None
    
    
def get_gmt_now():
    return datetime.datetime.fromtimestamp(time.mktime(time.gmtime()))
    
    
def format_date(d):
  return d.strftime("%a, %d %b %Y %H:%M:%S GMT")
  
  
def jsonify(require_content_type=False):
  from _app import app
  
  def wrapper(f):
    def handler(*args, **kwargs):
      if not require_content_type or (require_content_type and 'content_type' in kwargs
          and kwargs['content_type'] == 'json'):
      
        app.response.headers['Content-Type'] = 'application/json'
        return json.dumps(f(*args, **kwargs), cls=config.jsonify.encoder)
        
      else:
        return f(*args, **kwargs)
        
    handler.__name__ = f.__name__
    return handler
    
  return wrapper
  
  
class Pagination(object):
  def __init__(self, query, page=1, limit=20, max_limit=100):
    self.query = query
    self.page = int(page)
    self.limit = int(limit)
    self.max_limit = max_limit
    
    self.offset = (self.page-1) * self.limit
    self._count = None
    self._num_pages = None
    
  def __iter__(self):
    for i in self.query.offset(self.offset).limit(self.limit):
      yield i
      
  @property
  def count(self):
    if not self._count:
      self._count = self.query.count()
    return self._count
    
  @property
  def num_pages(self):
    if not self._num_pages:
      remainder = self.count % self.limit
      num_pages = self.count / self.limit
      if remainder:
        num_pages += 1
      self._num_pages = num_pages
    return self._num_pages
      
  @property
  def pages(self):
    pages = {}
    for i in xrange(1, self.num_pages + 1):
      yield {'num': i, 'selected': i == self.page}


class Hook(object):
  priority = 10
  
  def __init__(self, app, controller):
    self.app = app
    self.controller = controller


def import_all_from_folder(path, excludes=[]):
  import os
  import sys
  from importlib import import_module
  from glob import glob

  modules = {}
  base_path = os.path.dirname(path)

  if not os.path.exists(base_path):
    raise ImportError("Cannot import modules from %s. Path does not exist." % abs_path)

  add_path = base_path not in sys.path
    
  if add_path:
    sys.path.append(base_path)

  for file_path in glob('%s/*.py' % base_path):
    dir_name, file_name = os.path.split(file_path)
    module_name = file_name[:-3]
    modules[module_name] = import_module(module_name)

  if add_path:
    sys.path.remove(base_path)

  return modules


class MethodException(Exception):
  def __init__(self, action, params={}, *args, **kwargs):
    import _app
    import response

    if not action.im_self:
      obj = action.im_class()
      action = getattr(obj, action.__name__)

    self.response = response.Response(_app.app, action, params)

    Exception.__init__(self, *args, **kwargs)
