import sys, os


class HTTPError(Exception):
	def __init__(self, template=None):
		self.template = template or 'errors/%s.html' % self.code
		self.headers = {'Content-Type': 'text/html'}
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


class Error404(HTTPError):
	def __init__(self, message="File Not Found", *args, **kwargs):
		self.message = message
		self.code = 404
		HTTPError.__init__(self, *args, **kwargs)


class Error500(HTTPError):
	def __init__(self, message="Internal Server Error", *args, **kwargs):
		import traceback

		self.message = message
		self.code = 500
		HTTPError.__init__(self, *args, **kwargs)

		e_type, e_value, e_tb = sys.exc_info()
		if e_tb:
			self.parameters['traceback'] = traceback.format_exception(e_type, e_value, e_tb)
		else:
			self.parameters['traceback'] = None


class SessionLoadError(Exception):
	pass


class SessionSaveError(Exception):
	pass
