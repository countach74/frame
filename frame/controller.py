from _routes import routes
import _app
from errors import Error301, Error302, Error303


class _ControllerMeta(type):
	def __init__(cls, name, stuff, args):
		if name != 'Controller':
			routes.controllers[name.lower()] = cls
	
		type.__init__(cls, name, stuff, args)


class Controller(object):
	'''
	Controllers are a central part of Frame's methodology, even though they are extremely
	simple, programming-wise. From within a controller, you can directly access the Jinja2
	template engine, the current :mod:`frame.request.Request` and
	:mod:`frame.response.Response` objects, and also the session data. The goal is that
	for everyday tasks, you should not have to import a bunch of other frame objects or
	modules	into your controller logic.
	
	Actions (controller methods that have routes pointed to them) can return either string
	data to return as the response body or a dictionary to pass as values to the Jinja2
	template engine. It should be noted that by default, Frame assumes your templates
	will be located in the 'templates' directory of your application and will automatically
	try to resolve a controller action to ``templates/{controller_name}/{action_name}.html``,
	where both the names are lowercase versions of your controller and action.
	
	Consider the following::
	
		import frame
		
		class SomeController(frame.Controller):
			def do_something(self, name):
				return {'name': name}
				
	In this instance, Frame will assume that your template for 'SomeController.do_something'
	is located at 'templates/somecontroller/do_something.html' and it will automatically
	send off the ``{'name': name}`` dictionary to the template. Of course, this can be
	overridden. This is done by returning the template result directly::
	
		class SomeController(frame.Controller):
			def do_something(self, name):
				return self.get_template('path/to/template.html').render({'name': name})
				
	It should be noted that any return value that is not a dictionary and not a string
	will be converted to a string. :attr:`Controller.get_template`
	'''
	
	__metaclass__ = _ControllerMeta
	
	app = _app.app
	'''The current Frame application'''

	def redirect(self, url, add_script_name=True, status='302 Found'):
		'''
		A shortcut to raise a given error message; intended for use with 3xx HTTP messages.
		By default, raises '302 Found'.
		
		:param url: The URL to redirect to
		:param add_script_name: If true, tags the FastCGI script name to the beginning of
			the url; use for portability when appropriate
		:param status: The status line
		'''
		
		code, message = status.split(None, 1)
		code = int(code)
		
		if add_script_name and '://' not in url:
			url = self.app.request.headers.script_name + url
		
		error = globals()['Error%s' % code](url, message=message)
		
		raise error

	"""
	@property
	def response(self):
		'''
		Retrieve the current :mod:`frame.response.Response` object.
		'''
		return app.response
	"""

	@property
	def request(self):
		'''
		Retrieve the current :mod:`frame.request.Request` object.
		'''
		return self.app.request
		
	@property
	def uri(self):
		'''
		Get a list containing the URI elements, separated on '/'.
		'''
		return self.request.headers.path_info.strip('/').split('/')
