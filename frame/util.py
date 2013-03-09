'''
Some simple utilities to help out with everyday operations. Some of these
are used internally by Frame; some are designed to be used by web developers.
'''


import re
import types
from threading import RLock


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
				user_groups = frame.app.session['user']
				
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
	template_dir = re.sub("(/{.*?})", '', path)
	
	while template_dir.startswith('/'):
		template_dir = template_dir[1:]
	
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
	
		frame.config['logger.stdout.out'] = FileLogger('/tmp/framelog.out')
		frame.config['logger.stdout.err'] = FileLogger('/tmp/framelog.err')
		
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