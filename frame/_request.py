from _dotdict import DotDict
from _routes import routes


class Request(object):
	def __init__(self, environ):
		self.__environ = environ
		self.__parse(environ)

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
