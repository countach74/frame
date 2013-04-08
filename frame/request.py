from dotdict import DotDict
from _routes import routes
from _logger import logger


class Request(object):
	'''
	A simple parser for the WSGI environ dictionary.
	
	There really isn't much of interest here other than a handful of attributes that are
	very useful. Note that :mod:`frame._app.App` instantiates this class; its objects are
	made available in two locations: :attr:`frame._app.App.request` and
	:attr:`frame.controller.Controller.request`.
	'''
	
	def __init__(self, environ):
		self.environ = environ   #: The WSGI environment
		self.headers = DotDict()   #: Both FastCGI and HTTP headers
		self.http_headers = DotDict()   #: Dictionary of just HTTP headers
		self.wsgi = DotDict()   #: The WSGI objects
		
		self.__parse(environ)
		self.__body = None
		self.cookies = self.__parse_cookies(environ)   #: Parsed cookies

	def __parse(self, environ):
		for key, value in environ.items():
			if key.startswith('wsgi.'):
				parsed_key = key.split('.', 1)[1]
				self.wsgi[parsed_key] = value

			elif key.startswith('HTTP_'):
				parsed_key = key[5:].lower()
				self.headers[parsed_key] = value
				self.http_headers[parsed_key] = value

			else:
				parsed_key = key.lower()
				self.headers[parsed_key] = value

	def __parse_cookies(self, environ):
		result = DotDict()
		if 'HTTP_COOKIE' in environ:
			cookies = environ['HTTP_COOKIE'].split('; ')
			for i in cookies:
				try:
					key, value = i.strip().split('=', 1)
				except ValueError:
					continue
				else:
					result[key] = value
		return result

	@property
	def body(self):
		'''
		The request body
		'''
		if self.__body is None:
			self.__body = self.wsgi.input.read()
		return self.__body
