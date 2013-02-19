from errors import Error404, Error401
import re
import os
import mimetypes


class StaticDispatcher(object):
	def __init__(self, static_map):
		self.static_map = static_map
		self._resolve_map()

	def __getitem__(self, key):
		return self.static_map[key]

	def __setitem__(self, key, value):
		self.static_map[key] = os.path.abspath(value)

	def _resolve_map(self):
		for i in self.static_map:
			self.static_map[i] = os.path.abspath(self.static_map[i])

	def match(self, environ):
		for key, value in self.static_map.items():
			uri = environ['PATH_INFO']

			if uri.startswith(key):
				uri = uri[len(key):]

				while uri.startswith('/'):
					uri = uri[1:]

				file_path = os.path.join(value, uri)
				trash, extension = os.path.splitext(file_path)

				if os.path.exists(file_path) and file_path.startswith(value):
					try:
						headers = {'Content-Type': mimetypes.types_map[extension]}
					except KeyError:
						headers = {'Content-Type': 'text/plain'}
					try:
						response_body = open(file_path, 'r').read()
					except IOError:
						raise Error404

				else:
					continue

				return ('200 OK', headers, response_body)

		raise Error404
