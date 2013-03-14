import unittest
from StringIO import StringIO
from frame.request import Request


_request_body = "name=Bob%20The%20Builder"
_environ = {
	'wsgi.input': StringIO(_request_body),
	'wsgi.multithreaded': True,
	'wsgi.multiprocess': False,
	'HTTP_COOKIE': 'FrameSession=sahiosadnlk2n34o23asd',
	'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'HTTP_USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.22 '
		'(KHTML, like Gecko) Chrome/25.0.1364.160 Safari/537.22',
	'HTTP_ACCEPT_ENCODING': 'gzip,deflate,sdch',
	'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.8',
	'HTTP_CONTENT_TYPE': 'application/x-www-form-urlencoded',
	'REQUEST_URI': '/',
	'PATH_INFO': '/',
	'REQUEST_METHOD': 'POST',
}
		
		
class TestRequest(unittest.TestCase):
	def setUp(self):
		_environ['wsgi.input'].seek(0)
		self.request = Request(_environ)
		
	def test_cookies(self):
		assert self.request.cookies.FrameSession == 'sahiosadnlk2n34o23asd'
		
	def test_request_body(self):
		assert self.request.body == _request_body
		
		# Run a second time to ensure that the request.body property is functioning correctly
		assert self.request.body == _request_body
		
	def test_headers(self):
		for k, v in _environ.items():
			
			if k.startswith('HTTP_') or k.startswith('SERVER_'):
				key = k.split('_', 1)[1].lower()
				assert key in self.request.headers and v == self.request.headers[key]
				
			elif k.startswith('wsgi.'):
				key = k.split('.', 1)[1].lower()
				assert key in self.request.wsgi and v == self.request.wsgi[key]