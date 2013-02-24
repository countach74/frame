"""
Some simple utilities to help out with everyday operations. Some of these
are used internally by Frame; some are designed to be used by web developers.
"""


import re


def parse_query_string(string):
	from cgi import parse_qs

	data = parse_qs(string)
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