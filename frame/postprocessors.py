'''
Post processors are applied to the response body just before delivery to the client. This
is how simple things like "deflate" are implemented. A post processor is simply a callable
that accepts two parameters: the request and response objects. They are exactly what
they sound like. To learn how to implement a post processor, probably the best way is to
take a look at the :func:`deflate` source code below.
'''

import zlib
import datetime
import json
from util import format_date, get_gmt_now


def deflate(request, response):
	'''
	Sets response content-encoding to 'deflate' and uses zlib compression to compress the
	response body.
	
	:param request: The current :mod:`frame.request.Request` object
	:param response: The current :mod:`frame.response.Response` object
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
		
		
def add_last_modified(request, response):
	'''
	Ensures that all responses have a Last-Modified header.
	'''
	if 'Last-Modified' not in response.headers:
		response.headers['Last-Modified'] = format_date(get_gmt_now())


def add_date(request, response):
	'''
	Adds the current timestamp to all requests.
	'''
	response.headers['Date'] = format_date(get_gmt_now())
		
		
def jsonify(request, response):
	'''
	Assume that whenever the content_type kwarg is present and set to 'json', the response
	should be JSON encoded. This is for every request! If you only want to enable this sort
	of behavior on specific controller actions, use :func:`frame.util.jsonify`.
	'''
	params = dict(response.params.items() + response.additional_params.items())
	if 'content_type' in params and params['content_type'] == 'json':
		print 'JSON'
		response.headers['Content-Type'] == 'application/json'
		json_data = json.dumps(response.action(**params))
		response.body = json_data
		response.headers['Content-Length'] = len(json_data)
