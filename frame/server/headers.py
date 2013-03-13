import re
import sys
import os


class RequestMixin(object):
	def __init__(self, request):
		self._request = request
		self._data = self._parse(request)


class Headers(object):
	def __getitem__(self, key):
		return self._data[key]

	def __contains__(self, key):
		return key in self._data

	def __iter__(self):
		for i in self._data:
			yield i
			
	def _format_key(self, key):
		return key.replace("-", "_").upper()

	def items(self):
		return self._data.items()

	def get(self, *args, **kwargs):
		return self._data.get(*args, **kwargs)


class RequestHeaders(Headers, RequestMixin):
	__request_pattern = re.compile("([a-zA-Z0-9\-]+):\s+(.*)")

	def _parse(self, request):
		result = {}
		data = re.findall(self.__request_pattern, request)

		for k, v in data:
			result["HTTP_%s" % self._format_key(k)] = v.strip()
		return result
		
	def __repr__(self):
		return "<RequestHeaders(%s)>" % self._data


class RequestLine(Headers, RequestMixin):
	__request_line_pattern = re.compile("^([A-Z]+) ([\S]+) HTTP/([0-1\.]+)\r\n")
	
	def __repr__(self):
		return "<RequestLine('%s')>" % self._request

	def _parse(self, request):
		match = re.match(self.__request_line_pattern, request)

		if not match:
			raise ValueError("Invalid request line.")
			
		uri_split = match.group(2).split('?', 1)
		path_info = uri_split[0]
		query_string = uri_split[1] if len(uri_split) > 1 else ''

		return {
			'REQUEST_METHOD': match.group(1),
			'REQUEST_URI': match.group(2),
			'PATH_INFO': path_info,
			'QUERY_STRING': query_string,
		}
