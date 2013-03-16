from errors import Error404, Error401
import re
import os
import mimetypes
import datetime
import time
from util import format_date
from dotdict import DotDict
from _config import config
from response import Response


class StaticDispatcher(object):
	def __init__(self, app, static_map=None):
		self.app = app
		self.static_map = static_map if static_map else {}
		self._resolve_map()

	def __getitem__(self, key):
		return self.static_map[key]

	def __setitem__(self, key, value):
		self.static_map[key] = os.path.abspath(value)

	def __repr__(self):
		return "Static Dispatcher: %s" % self.static_map

	def _resolve_map(self):
		for i in self.static_map:
			self.static_map[i] = os.path.abspath(self.static_map[i])
			
	def read_file(self, filepath):
		f = open(filepath, 'r')
		data = f.read(4096)
		while data:
			yield data
			data = f.read(4096)

	def match(self, environ):
		for key, value in self.static_map.items():
			uri = environ['PATH_INFO']

			if uri.startswith(key):
				uri = uri[len(key):]
				uri = uri.lstrip('/')

				file_path = os.path.join(value, uri)
				trash, extension = os.path.splitext(file_path)
				
				headers = dict(config.response.default_headers)

				if os.path.exists(file_path) and file_path.startswith(value):
					try:
						headers['Content-Type'] = mimetypes.types_map[extension]
					except KeyError:
						headers['Content-Type'] = 'application/octet-stream'
					try:
						response_body = self.read_file(file_path)
					except EnvironmentError:
						raise Error401

				else:
					continue
				
				try:
					st = os.stat(file_path)
				except EnvironmentError, e:
					pass
				else:
					last_modified = datetime.datetime.fromtimestamp(
						time.mktime(time.gmtime(st.st_mtime)))
					headers['Last-Modified'] = format_date(last_modified)

				self.app.response = Response.from_data('200 OK', headers, response_body)
				return self.app.response

		raise Error404
