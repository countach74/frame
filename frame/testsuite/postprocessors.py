import unittest
import zlib
from StringIO import StringIO
from request import _environ
from response import Controller
from frame.request import Request
from frame.response import Response
from frame._app import app
from frame.postprocessors import deflate, handle_head_request, add_last_modified


class TestPostprocessors(unittest.TestCase):
	def setUp(self):
		_environ['wsgi.input'].seek(0)
		self.request = Request(_environ)
		self.response = Response(app, Controller().string_no_args)
		
	def test_deflate(self):
		encoded_string = zlib.compress("Hello, world!")
		response_body = self.response.render('', {})
		response_body = deflate(self.request, self.response, response_body)
		assert encoded_string == response_body
		assert self.response.headers['Content-Encoding'] == 'deflate'
		assert self.response.headers['Content-Length'] == str(len(encoded_string))
		
	def test_handle_head_request(self):
		environ = dict(_environ)
		environ['REQUEST_METHOD'] = 'HEAD'
		environ['wsgi.input'] = StringIO()
		request = Request(environ)
		response_body = self.response.render('', {})
		response_body = handle_head_request(request, self.response, response_body)
		assert response_body == '' and self.response.headers['Content-Length'] == '0'
		
	def test_add_last_modified(self):
		response_body = self.response.render('', {})
		response_body = add_last_modified(self.request, self.response, response_body)
		assert 'Last-Modified' in self.response.headers