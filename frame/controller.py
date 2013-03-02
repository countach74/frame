from _routes import routes
from _app import app
from errors import Error301, Error302, Error303


class _ControllerMeta(type):
	def __init__(cls, name, stuff, args):
		if name != 'Controller':
			routes.controllers[name.lower()] = cls()
	
		type.__init__(cls, name, stuff, args)


class Controller(object):
	__metaclass__ = _ControllerMeta
	app = app

	def redirect(self, url, add_script_name=True, status='301 Moved Permanently'):
		code, message = status.split(None, 1)
		code = int(code)
		
		if add_script_name and '://' not in url:
			url = self.app.request.headers.script_name + url
		
		error = globals()['Error%s' % code](url, message=message)
		
		raise error

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