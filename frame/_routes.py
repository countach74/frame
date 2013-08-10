import re
import os
from routes import Mapper
from uuid import uuid4
from util import make_resource, Singleton
from _logger import logger
import threading
import _app


class Routes(Singleton):
	'''
	A wrapper around :class:`routes.mapper.Mapper`. Allows for easily mapping URI patterns to a
	given controller action. This is a :mod:`frame.util.Singleton` class and as such can
	only be instantiated once (any subsequent instances will actually point to the same
	object as the first).
	
	Frame automatically instantiates the Routes object; the main reference to it should be
	accessed via :attr:`frame.routes`.
	
	Basic URI's can be connected like so::
	
		import frame
		
		frame.routes.connect('/', 'root#index')
		frame.routes.connect('/about', 'root#about')
		frame.routes.connect('/contact', 'root#contact')
		
	... where ``root`` is the lowercased name of a controller defined prior. The hash mark
	(``#``) is used as a delimiter between the controller name and the action method. In
	other words, ``root#about`` would call Root.about().
	
	If we want to use some sort of slug to say, access a user, we could do this::
	
		frame.routes.connect('/users/{username}', 'users#show')
		
	... which will call Users.show(username) where username is whatever was passed via the
	request URI.
	
	When scaling up from a hello world application to something much more involved, RESTful
	principles can be very helpful (if you are not familiar with REST/RESTful, I suggest
	visiting http://en.wikipedia.org/wiki/Representational_state_transfer). To make your
	life easier, :meth:`resource` defines all of the common RESTful methods for you for a
	given controller.
	
	Consider::
	
		import frame
		
		class Users(frame.Controller):
			def index(self):
				return {'users': get_all_users()}
				
			def show(self, slug):
				return {'user': get_user(slug)}
				
			def new(self):
				pass
				
			def create(self, **data):
				create_user(**data)
				
			def edit(self, slug):
				return {'user': get_user(slug)}
				
			def update(self, slug, **data):
				update_user(slug, **data)
				return {'user': slug}
				
			def delete(self, slug):
				delete_user(slug)
				
	Obviously, this is an overly simplified controller that is designed to perform CRUD
	operations on a user. If we want to map all of these controller methods to appropriate
	URI's, we can use the :meth:`resource`::
	
		frame.routes.resource('users')
		
	... and the following associations will be made:
	
	+--------------------+--------+--------------------+
	| URI                | Method | Action             |
	+====================+========+====================+
	| /users             | GET    | Users.index        |
	+--------------------+--------+--------------------+
	| /users/{slug}      | GET    | Users.show         |
	+--------------------+--------+--------------------+
	| /users/new         | GET    | Users.new          |
	+--------------------+--------+--------------------+
	| /users             | POST   | Users.create       |
	+--------------------+--------+--------------------+
	| /users/{slug}/edit | GET    | Users.edit         |
	+--------------------+--------+--------------------+
	| /users/{slug}      | POST   | Users.update       |
	+--------------------+--------+--------------------+
	| /users/{slug}      | DELETE | Users.delete       |
	+--------------------+--------+--------------------+
	
	Additionally, if you don't want to register all of the mappings at ``/users``, but say
	``/admin/users``, you can do this instead::
	
		frame.routes.resource('users', '/admin/users')
		
	The resource handling is similar to how :mod:`routes` works but not identical.
	Nevertheless, I do recommend reading up on :mod:`routes` documentation for more
	information.
	'''
	
	def __init__(self):
		self.mapper = Mapper()
		self.controllers = {}
		self.resources = {}

		# Setup to use sub domains by default
		self.mapper.sub_domains = True
		
	@property
	def thread_data(self):
		return _app.app.thread_data
		
	def register_controller(self, controller):
		'''
		Registers a controller to the routes object. This is handled automatically whenever
		:mod:`frame.controller.Controller` is subclassed.
		
		:param controller: A :mod:`frame.controller.Controller`
		'''
		self.controllers[controller.__class__.__name__.lower()] = controller

	def match(self, *args, **kwargs):
		'''
		Matches a request (typical via the WSGI environ dictionary) to a controller/action.
		If no match is found, None is returned; else, a tuple containing the action and the
		raw :mod:`routes` match data is returned.
		'''
		match = self.mapper.match(*args, **kwargs)

		# Python routes likes to maintain the 'sub_domain' argument from conditionals,
		# which doesn't work very well with Frame's setup, so we remove it.
		if 'sub_domain' in match:
			del(match['sub_domain'])

		if match:
			if not hasattr(match['action'], '__call__'):
				controller = self.controllers[match['controller']]()
				action = getattr(controller, match['action'])
			else:
				action = match['action']
				controller = None
				
			self.thread_data['current_route'] = {
				'controller': controller,
				'action': action
			}
			
			return (action, match)

		else:
			return None
			
	@property
	def current_controller(self):
		return self.thread_data['current_route']['controller']

	@property
	def current_action(self):
		return self.thread_data['current_route']['action']
		
	def connect(self, path, controller=None, *args, **kwargs):
		'''
		Connect a URI pattern to a controller.
		
		:param path: The URI path to match with
		:param controller: A string containing the controller and action
		'''
		name = uuid4()

		if '#' in controller:
			controller, action = controller.split('#', 1)
		else:
			action = 'index'

		self.mapper.connect(name, path, controller=controller, action=action, *args, **kwargs)
		
	def parse_mount_point(self, mount_point):
		regex = re.compile("(/{.*?})")
		return re.sub(regex, '', mount_point)
		
	def expose(self, controller, mount_point=None):
		'''
		Creates simple routes for all callable attributes of the given controller.
		
		:param controller: A lower case representation of the controller to create routes for
		:param mount_point: If specified, allows specification of the prefix to use. If not
			specified, assumes '/{controller_name}' as the prefix
		'''
		if not mount_point:
			mount_point = '/%s' % controller
			
		controller_object = self.controllers[controller]
		
		candidates = (i for i in dir(controller_object) if not i.startswith('_'))
		for i in candidates:
			try:
				method = getattr(controller_object, i)
			except AttributeError:
				continue
			else:
				if hasattr(method, '__call__'):
					method_mount_point = os.path.join(mount_point, i)
					self.connect(method_mount_point, '%s#%s' % (controller, i))
		
		self.connect(mount_point, '%s#index' % controller)
		
	def resource(self, controller, mount_point=None):
		'''
		Defines a RESTful resource for the controller.
		'''
		if not mount_point:
			mount_point = '/%s' % controller
		
		uri_map = [
			{
				'uri': '%s.{content_type}',
				'action': 'index',
				'method': 'GET',
			},
			{
				'uri': '%s',
				'action': 'index',
				'method': 'GET',
			},
			{
				'uri': '%s.{content_type}',
				'action': 'create',
				'method': 'POST'
			},
			{
				'uri': '%s',
				'action': 'create',
				'method': 'POST',
			},
			{
				'uri': '%s/new.{content_type}',
				'action': 'new',
				'method': 'GET'
			},
			{
				'uri': '%s/new',
				'action': 'new',
				'method': 'GET',
			},
			{
				'uri': '%s/{slug}.{content_type}',
				'action': 'update',
				'method': 'POST',
			},
			{
				'uri': '%s/{slug}',
				'action': 'update',
				'method': 'POST',
			},
			{
				'uri': '%s/{slug}.{content_type}',
				'action': 'delete',
				'method': 'DELETE',
			},
			{
				'uri': '%s/{slug}',
				'action': 'delete',
				'method': 'DELETE',
			},
			{
				'uri': '%s/{slug}.{content_type}',
				'action': 'show',
				'method': 'GET',
			},
			{
				'uri': '%s/{slug}',
				'action': 'show',
				'method': 'GET',
			},
			{
				'uri': '%s/{slug}.{content_type}/edit',
				'action': 'edit',
				'method': 'GET',
			},
			{
				'uri': '%s/{slug}/edit',
				'action': 'edit',
				'method': 'GET',
			},
		]

		for i in uri_map:
			self.connect(
				path=i['uri'] % mount_point,
				controller='%s#%s' % (controller, i['action']),
				conditions={'method': i['method']})
				
		# Was a bad idea, trying without...
		#make_resource(self.controllers[controller], mount_point)
				

routes = Routes()
