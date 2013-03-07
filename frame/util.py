"""
Some simple utilities to help out with everyday operations. Some of these
are used internally by Frame; some are designed to be used by web developers.
"""


import re
import types
from threading import RLock


class Decorator(object):
	def __get__(self, instance, parent=None):
		return types.MethodType(self, instance)
		
		
class Authorization(Decorator):
	def __init__(self, groups=[], users=[]):
		self.groups = groups
		self.users = users
		
	def __call__(self, f):
		def auth(*args, **kwargs):
			return self.authorize(f, *args, **kwargs)
			
		# Fix the auto-template routing issue w/decorators
		auth.__name__ = f.__name__
		
		return auth


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
	if len(text) > length:
		first_half = text[0:length/2]
		second_half = text[-length/2:]
		return "%s...%s" % (first_half, second_half)
	else:
		return text


class FileLogger(object):
	def __init__(self, path):
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