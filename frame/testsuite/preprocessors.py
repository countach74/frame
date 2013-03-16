import unittest
from StringIO import StringIO
from request import _environ
from response import Controller
from frame.request import Request
from frame.response import Response
from frame._app import app
from frame.preprocessors import (form_url_decoder, form_json_decoder,
	form_multipart_decoder, handle_query_string)


class TestPreprocessors(unittest.TestCase):
	def setUp(self):
		_environ['wsgi.input'].seek(0)
		self.request = Request(_environ)
		self.response = Response(app, Controller().string_no_args)
		
	def test_form_url_decoder(self):
		data = {'name': 'Bob The Builder'}
		form_url_decoder(self.request, self.response)
		assert self.response.additional_params == data
		
	def test_form_json_decoder(self):
		data = {'name': 'Bob The Builder'}
		environ = dict(_environ)
		environ.update({
			'HTTP_CONTENT_TYPE': 'application/json',
			'wsgi.input': StringIO('{"name": "Bob The Builder"}')
		})
		request = Request(environ)
		
		form_json_decoder(request, self.response)
		assert self.response.additional_params == data
		
	def test_form_multipart_decoder(self):
		'''
		Argh, skipping this one for now...
		'''
		pass
	
	def test_handle_query_string(self):
		environ = dict(_environ)
		environ.update({
			'QUERY_STRING': 'data=some_data'
		})
		request = Request(environ)
		
		handle_query_string(request, self.response)
		assert self.response.additional_params == {'data': 'some_data'}
