import frame
import types


class Auth(object):
	def __init__(self, f):
		self.f = f

	def __get__(self, instance, parent):
		self.controller = instance
		return types.MethodType(self, instance, parent)

	def __call__(self, *args, **kwargs):
		import session
		if 'groups' not in session or 'admin' not in session['groups']:
			self.controller.redirect('/login')
		else:
			return self.f(*args, **kwargs)


frame.Auth = Auth
