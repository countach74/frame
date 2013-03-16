import unittest
import frame
from routes import Mapper


class TestConnect(unittest.TestCase):
	def setUp(self):
		frame.routes.mapper = Mapper()
		
		class Connect(frame.Controller):
			def get_action(self):
				return 'connect.action.get'
			
			def post_action(self):
				return 'connect.action.post'
				
			def put_action(self):
				return 'connect.action.put'
				
			def delete_action(self):
				return 'connect.action.delete'
				
		frame.routes.connect('/action', 'connect#get_action', conditions={'method': 'GET'})
		frame.routes.connect('/action', 'connect#post_action', conditions={'method': 'POST'})
		frame.routes.connect('/action', 'connect#put_action', conditions={'method': 'PUT'})
		frame.routes.connect('/action', 'connect#delete_action', conditions={'method': 'DELETE'})
		frame.routes.connect('/invalid_controller', 'invalid#action')
		
		
	def render(self, method, path='/action', **kwargs):
		match = frame.routes.match(environ={
			'REQUEST_METHOD': method.upper(),
			'PATH_INFO': path
		})
		assert match
		return match[0](**kwargs)
		
	def test_get(self):
		assert self.render('get') == 'connect.action.get'
		
	def test_post(self):
		assert self.render('post') == 'connect.action.post'
		
	def test_put(self):
		assert self.render('put') == 'connect.action.put'
		
	def test_delete(self):
		assert self.render('delete') == 'connect.action.delete'
		
	def test_invalid_arg(self):
		with self.assertRaisesRegexp(TypeError, 'unexpected keyword argument'):
			self.render('get', name='bob')
			
	def test_invalid_controller(self):
		with self.assertRaises(KeyError):
			frame.routes.match('/invalid_controller')
			
	def test_not_found(self):
		match = frame.routes.match('/not_found')
		assert match is None
			
			
class TestResource(unittest.TestCase):
	def setUp(self):
		frame.routes.mapper = Mapper()
		
		class Resource(frame.Controller):
			def index(self):
				return 'resource.index'
				
			def show(self, slug):
				return 'resource.show.%s' % slug
				
			def new(self):
				return 'resource.new'
				
			def create(self, name):
				return 'resource.create.%s' % name
				
			def edit(self, slug):
				return 'resource.edit.%s' % slug
				
			def update(self, slug, name):
				return 'resource.update.%s.%s' % (slug, name)
				
			def delete(self, slug):
				return 'resource.delete.%s' % slug
				
		frame.routes.resource('resource')
		
	def render(self, uri, method, **kwargs):
		match = frame.routes.match(environ={
			'PATH_INFO': uri,
			'REQUEST_METHOD': method.upper()
		})
		assert match
		
		extra_args = dict(**kwargs)
		for k, v in match[1].iteritems():
			if k not in ('controller', 'action'):
				extra_args[k] = v
		
		return match[0](**extra_args)
		
	def test_index(self):
		assert self.render('/resource', 'get') == 'resource.index'
		
	def test_show(self):
		assert self.render('/resource/item', 'get') == 'resource.show.item'
		
	def test_new(self):
		assert self.render('/resource/new', 'get') == 'resource.new'
		
	def test_create(self):
		assert self.render('/resource', 'post', name='test') == 'resource.create.test'
		
	def test_edit(self):
		assert self.render('/resource/item/edit', 'get') == 'resource.edit.item'
		
	def test_update(self):
		assert self.render('/resource/item', 'post', name='test') == 'resource.update.item.test'
		
	def test_delete(self):
		assert self.render('/resource/item', 'delete') == 'resource.delete.item'