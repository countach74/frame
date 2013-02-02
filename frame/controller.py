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

	def get_template(self, *args, **kwargs):
		return self.app.environment.get_template(*args, **kwargs)

	@property
	def response(self):
		return app.response

	@property
	def request(self):
		return app.request
