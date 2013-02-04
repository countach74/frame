from _routes import routes
from _app import app


class _ControllerMeta(type):
	def __init__(cls, name, stuff, args):
		if name != 'Controller':
			routes.controllers[name.lower()] = cls()
	
		type.__init__(cls, name, stuff, args)


class Controller(object):
	__metaclass__ = _ControllerMeta
	app = app

	def redirect(self, url, status='301 Moved Permanently'):
		self.response.status = status
		self.response.headers['Location'] = url

	@property
	def get_template(self):
		return self.app.environment.get_template

	@property
	def response(self):
		return app.response

	@property
	def request(self):
		return app.request

	@property
	def session(self):
		return app.session
