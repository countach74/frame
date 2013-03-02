import sys, os
from cgi import escape
from _logger import logger


class HTTPError(Exception):
	def __init__(self, template=None, headers={'Content-Type': 'text/html'}):
		self.template = template or 'errors/%s.html' % self.code
		self.headers = headers
		self.parameters = {}

	def render(self, app):
		self.app = app
		return (
			self.status,
			self.headers,
			app.environment.get_template('errors/%s.html' % self.code).render(**self.get_parameters()))

	def get_parameters(self):
		defaults = {
			'message': self.message,
			'status': self.status,
			'code': self.code,
			'app': self.app
		}
		return dict(defaults.items() + self.parameters.items())

	@property
	def status(self):
		return "%s %s" % (self.code, self.message)
		

# HTTP 3xx Errors
class Error301(HTTPError):
	def __init__(self, url, message='301 Moved Permanently', *args, **kwargs):
		self.url = url
		self.message = message
		self.code = 301
		HTTPError.__init__(self, *args, **kwargs)
		
		self.headers = {
			'Location': self.url
		}
		
	def render(self, app):
		self.app = app
		return (
			self.status,
			self.headers,
			None)
			
			
class Error302(Error301):
	pass


class Error303(Error301):
	pass


# HTTP 4xx Errors
class Error404(HTTPError):
	def __init__(self, message="File Not Found", *args, **kwargs):
		self.message = message
		self.code = 404
		HTTPError.__init__(self, *args, **kwargs)


class Error401(Error404):
	def __init__(self, message="Not Authorized", *args, **kwargs):
		Error404.__init__(self, message, *args, **kwargs)
		self.code = 401


class Error403(Error404):
	def __init__(self, message="Forbidden", *args, **kwargs):
		Error404.__init__(self, message, *args, **kwargs)
		self.code = 403


# HTTP 5xx Errors
class Error500(HTTPError):
	def __init__(self, message="Internal Server Error", *args, **kwargs):
		import traceback

		self.message = message
		self.code = 500
		HTTPError.__init__(self, *args, **kwargs)

		e_type, e_value, e_tb = sys.exc_info()
		if e_tb:
			tb = traceback.format_exception(e_type, e_value, e_tb)
			self.parameters['traceback'] = map(escape, tb)
			for line in tb:
				sys.stderr.write(line)
				logger.log_exception(line)
		else:
			self.parameters['traceback'] = None


class SessionLoadError(Exception):
	pass


class SessionSaveError(Exception):
	pass
