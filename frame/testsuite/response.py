import unittest
import frame
import re
from datetime import timedelta
from frame.util import get_gmt_now, format_date
from frame.response import Response
from jinja2 import Environment, PackageLoader


class Controller(frame.Controller):
	def string_no_args(self):
		return "Hello, world!"
		
	def string_args(self, data):
		return "Test: %s" % data
		
	def dictionary_no_args(self):
		return {'this': 'that'}
		
	def dictionary_args(self, data):
		return {'this': data}
		
		
class TestResponse(unittest.TestCase):
	def setUp(self):
		self.controller = Controller()
		self.app = frame.app
		self.app.environment = Environment(loader=PackageLoader('frame', 'testsuite/templates'))
		
	def test_no_controller(self):
		with self.assertRaises(frame.Error404):
			response = Response(self.app, None)
			
	def test_string_no_args(self):
		response = Response(self.app, self.controller.string_no_args)
		assert 'Hello, world!' == response.body
			
	def test_dictionary_no_args(self):
		response = Response(self.app, self.controller.dictionary_no_args)
		
	def test_string_args(self):
		response = Response(self.app, self.controller.string_args, {'data': 'some data'})
		assert 'Test: some data' == response.body
		
	def test_dictionary_args(self):
		response = Response(self.app, self.controller.dictionary_args, {'data': 'some data'})
		assert 'Test: some data' == response.body
		
	def test_set_cookie(self):
		response = Response(self, self.controller.string_no_args)
		expire_time = get_gmt_now() + timedelta(hours=1)
		expire_string = format_date(expire_time)
		response.set_cookie('some_cookie', 'some_data_for_cookie', 1)
		cookie_string = 'some_cookie=some_data_for_cookie; Expires=%s; Path=/' % expire_string
		assert cookie_string == response.headers['Set-Cookie']
		
	def test_delete_cookie(self):
		response = Response(self, self.controller.string_no_args)
		cookie_string = 'some_cookie=deleted; Expires=Thu, Jan 01 1970 00:00:00 GMT'
		response.delete_cookie('some_cookie')
		assert cookie_string == response.headers['Set-Cookie']
