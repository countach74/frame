import unittest
from routes.mapper import Mapper
import frame


class TestApp(unittest.TestCase):
	def setUp(self):
		frame.config.logger.driver = 'null'
		frame.app._prep_start()
		frame.routes.mapper = Mapper()
		
		class Root(frame.Controller):
			def string(self):
				return 'basic string output'
				
			def error(self):
				return invalid_name
				
		frame.routes.connect('/string', 'root#string')
		frame.routes.connect('/error', 'root#error')
		
	def start_response(self, status, headers):
		self.status = status
		self.headers = dict(headers)
		
	def test_dispatch_error(self):
		environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/error'}
		with self.assertRaises(frame.Error500):
			frame.app._dispatch(environ)
			
	def test_dispatch_string(self):
		environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/string'}
		response = frame.app._dispatch(environ)
		assert response.status == '200 OK'
		assert response.body == 'basic string output'
		
	def test_call_error(self):
		environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/error'}
		output = ''.join(frame.app(environ, self.start_response))
		assert self.status == '500 Internal Server Error'
		
	def test_call_string(self):
		environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/string'}
		output = ''.join(frame.app(environ, self.start_response))
		assert self.status == '200 OK'
		assert output == 'basic string output'
		assert str(len(output)) == self.headers['Content-Length']
