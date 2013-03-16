'''
Post processors are applied to the response body just before delivery to the client. This
is how simple things like "deflate" are implemented. A post processor is simply a callable
that accepts three parameters: request, response, response_body. They are exactly what
they sound like. To learn how to implement a post processor, probably the best way is to
take a look at the :func:`deflate` source code below.
'''

import zlib
import datetime
from util import format_date, get_gmt_now


def deflate(request, response):
	'''
	Sets response content-encoding to 'deflate' and uses zlib compression to compress the
	response body.
	
	:param request: The current :mod:`frame.request.Request` object
	:param response: The current :mod:`frame.response.Response` object
	:return: Compressed response_body
	'''
	
	if 'accept_encoding' in request.headers:
		if 'deflate' in request.headers.accept_encoding.split(','):
			if response.body:
				compressed = zlib.compress(response.body)
				response.headers['Content-Encoding'] = 'deflate'
				response.headers['Content-Length'] = str(len(compressed))
				response.body = compressed


def handle_head_request(request, response):
	'''
	Chops the response body off of HEAD requests
	'''
	
	if request.headers.request_method == 'HEAD':
		response.headers['Content-Length'] = '0'
		response.body = ''
	else:
		response.headers['Content-Length'] = str(len(response.body))
		
		
def add_last_modified(request, response):
	'''
	Ensures that all responses have a Last-Modified header.
	'''
	if 'Last-Modified' not in response.headers:
		response.headers['Last-Modified'] = format_date(get_gmt_now())