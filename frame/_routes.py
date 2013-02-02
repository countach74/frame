from routes import Mapper
from uuid import uuid4


class Routes(object):
	def __init__(self):
		self.mapper = Mapper()
		self.controllers = {}

	def register_controller(self, controller):
		self.controllers[controller.__class__.__name__.lower()] = controller()

	def match(self, *args, **kwargs):
		match = self.mapper.match(*args, **kwargs)
		if match:
			controller = self.controllers[match['controller']]
			action = getattr(controller, match['action'])
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
		

routes = Routes()
