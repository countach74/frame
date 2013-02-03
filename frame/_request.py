from _dotdict import DotDict
from _routes import routes


class Request(object):
	def __init__(self, environ):
		self.__environ = environ
		self.__parse(environ)
		self.__body = None
		self.cookies = self.__parse_cookies(environ)

	def __parse(self, environ):
		self.headers = DotDict()
		self.wsgi = DotDict()
		self.fcgi = DotDict()

		for key, value in environ.items():
			if key.startswith('wsgi.'):
				parsed_key = key.split('.', 1)[1]
				self.wsgi[parsed_key] = value

			elif key.startswith('HTTP_'):
				parsed_key = key[5:].lower()
				self.headers[parsed_key] = value

			else:
				parsed_key = key.lower()
				self.fcgi[parsed_key] = value

	def __parse_cookies(self, environ):
		result = DotDict()
		if 'HTTP_COOKIE' in environ:
			cookies = environ['HTTP_COOKIE'].split('; ')
			for i in cookies:
				key, value = i.strip().split('=', 1)
				result[key] = value
		return result

	@property
	def body(self):
		if self.__body is None:
			self.__body = self.wsgi.input.read()
		return self.__body
