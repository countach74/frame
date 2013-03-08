import re
from routes import Mapper
from uuid import uuid4
from util import make_resource, Singleton


class Routes(Singleton):
	def __init__(self):
		self.mapper = Mapper()
		self.controllers = {}
		self.resources = {}

	def register_controller(self, controller):
		self.controllers[controller.__class__.__name__.lower()] = controller()

	def match(self, *args, **kwargs):
		match = self.mapper.match(*args, **kwargs)
		if match:
			controller = self.controllers[match['controller']]
			action = getattr(controller, match['action'])
			self.current_controller = controller
			self.current_action = action
			return (action, match)

		else:
			return None

	def connect(self, path, controller=None, *args, **kwargs):
		name = uuid4()

		if '#' in controller:
			controller, action = controller.split('#', 1)
		else:
			action = 'index'

		self.mapper.connect(name, path, controller=controller, action=action, *args, **kwargs)
		
	def parse_mount_point(self, mount_point):
		regex = re.compile("(/{.*?})")
		return re.sub(regex, '', mount_point)
		
	def resource(self, controller, mount_point=None):
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
				'uri': '%s/{slug}',
				'action': 'update',
				'method': 'POST',
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
				
		make_resource(self.controllers[controller], mount_point)
				
		#self.resources[self.controllers[controller].__class__] = self.parse_mount_point(mount_point)

routes = Routes()
