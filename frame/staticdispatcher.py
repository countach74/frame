from errors import Error404, Error401, Error400, Error416
import re
import os
import mimetypes
import datetime
import time
from util import format_date, get_gmt_now
from dotdict import DotDict
from _config import config
from response import Response
from random import getrandbits


class StaticDispatcher(object):
	'''
	Establishes mount points for static files and then checks if those mount points are
	valid for a given request. If they are, serves files or throws 404.
	
	The use of this class is handled internally by Frame. Direct interaction with it is
	generally unnecessary and ill-advised. If you would like to add static mappings, please
	do it via `config.static_map`. For example::
	
		frame.config.static_map.update({
			'/scripts': '/path/to/scripts',
			'/styles': '/path/to/styles'
		})
	'''

	ranges_pattern = re.compile('^bytes=([0-9\-,]+)$', re.I)
	range_pattern = re.compile('^([0-9]+)-([0-9]*)$')
	negative_range_pattern = re.compile('^(-[0-9]+)$')
	
	def __init__(self, app, static_map=None):
		'''
		Initialize the static dispatcher.
		
		:param app: The Frame application
		:param static_map: A dictionary of static maps to use initially
		'''
		
		self.app = app
		self.static_map = static_map if static_map else {}
		self._resolve_map()
		
		# Need to initialize mimetypes only very basic types will be known
		mimetypes.init()

	def __getitem__(self, key):
		'''
		Returns the local path to a requested URI map.
		'''
		return self.static_map[key]

	def __setitem__(self, key, value):
		'''
		Sets a static map.
		
		For example::
			
			static_map['/scripts'] = '/path/to/scripts'
		'''
		self.static_map[key] = os.path.abspath(value)

	def __iter__(self):
		for i in static_map:
			yield i

	def __repr__(self):
		return "<Static Dispatcher: %s>" % self.static_map

	def items(self):
		return self.static_map.items()

	def _resolve_map(self):
		for i in self.static_map:
			self.static_map[i] = os.path.abspath(self.static_map[i])

	def get_boundary_string(self):
		return '%02x' % getrandbits(64)

	def make_boundary(self, boundary_string, content_type, start, position, file_length):
		return '\r\n'.join((
			'',
			'--%s' % boundary_string,
			'Content-Range: bytes %s-%s/%s' % (start, position, file_length),
			'Content-Type: %s' % content_type,
			''
		))
			
	def read_file(self, f, ranges=None, boundary_string=None):
		if ranges:
			f.seek(0, 2)
			file_length = f.tell()

			junk, extension = os.path.splitext(f.name)
			try:
				content_type = mimetypes.types_map[extension]
			except KeyError:
				content_type = 'application/octet-stream'

			for r in ranges:
				byte_range = self.range_pattern.match(r)
				if byte_range:
						start = int(byte_range.group(1))
						end = None if byte_range.group(2) == '' else int(byte_range.group(2)) + 1

						f.seek(start)
						position = f.tell()
						chunk_size = 4096 if end is None or end - position > 4096 else end - position

						# Setup first chunk
						data = f.read(chunk_size)

						if len(ranges) > 1:
							yield self.make_boundary(boundary_string, content_type, start, position, file_length)

						while data and (position < end if end is not None else True):
							if len(ranges) > 1:
								yield '%s\r\n' % data
							else:
								yield data

							data = f.read(chunk_size)

							position = f.tell()
							chunk_size = 4096 if end is None or end - position > 4096 else end - position

				else:
					negative_byte_range = self.negative_range_pattern.match(r)
					if negative_byte_range:
						start = int(negative_byte_range.group(1))

						f.seek(start, 2)

						data = f.read(4096)
						while data:
							yield data
							data = f.read(4096)

			if len(ranges) > 1:
				yield '--%s--\r\n' % boundary_string

		else:
			data = f.read(4096)
			first_run = True

			while first_run or data:
				yield data
				data = f.read(4096)
				first_run = False

	def get_range(self, f, r):
		range_match = self.range_pattern.match(r)
		if range_match:
			f.seek(0, 2)
			start = range_match.group(1)
			file_length = f.tell()
			if range_match.group(2) == '':
				end = file_length - 1
			else:
				end = int(range_match.group(2))
			return (start, end, file_length)

	def match(self, environ):
		'''
		Checks the WSGI environment provided to see if the requested path exists within the
		static mappings. If it does, returns the file; else, throws ``404 Not Found``.
		
		:param environ: WSGI environment (uses `PATH_INFO`)
		:param return: Returns a :class:`frame.response.Response` with the appropriate
			content-type, body, etc.
		'''
		
		for key, value in self.static_map.items():
			# Fix trouble caused by multiple preceeding '/'
			uri = '/%s' % environ['PATH_INFO'].lstrip('/')
			
			if uri.startswith(key):
				uri = uri[len(key):]
				uri = uri.lstrip('/')
				status = '200 OK'

				file_path = os.path.join(value, uri).rstrip('/')
				trash, extension = os.path.splitext(file_path)
				
				headers = dict(config.response.default_headers)

				if os.path.exists(file_path) and file_path.startswith(value):
					headers['Date'] = format_date(get_gmt_now())

					try:
						headers['Content-Type'] = mimetypes.types_map[extension]
					except KeyError:
						headers['Content-Type'] = 'application/octet-stream'

					try:
						headers['Accept-Ranges'] = 'bytes'

						if 'range' in self.app.request.headers:
							range_match = self.ranges_pattern.match(self.app.request.headers.range)
							if range_match:
								ranges = range_match.group(1).split(',')
								if False: #ranges[0] == '0-':
									response_body = self.read_file(open(file_path, 'r'))
								else:
									status = '206 Partial Content'
									boundary_string = self.get_boundary_string()
									file_obj = open(file_path, 'r')

									file_obj.seek(0, 2)

									if len(ranges) == 1:
										temp_range = self.get_range(file_obj, ranges[0])
										headers['Content-Range'] = 'bytes %s-%s/%s' % temp_range
									else:
										headers['Content-Type'] = 'multipart/byteranges; boundary=%s' % boundary_string

									response_body = self.read_file(file_obj, ranges, boundary_string)
							else:
								raise Error416
						else:
							response_body = self.read_file(open(file_path, 'r'))

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

				response = Response.from_data(status, headers, response_body)
				return response

		raise Error404
