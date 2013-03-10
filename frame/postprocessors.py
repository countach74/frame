'''
Post processors are applied to the response body just before delivery to the client. This
is how simple things like "deflate" are implemented. A post processor is simply a callable
that accepts three parameters: request, response, response_body. They are exactly what
they sound like. To learn how to implement a post processor, probably the best way is to
take a look at the :func:`deflate` source code below.
'''

import zlib


def deflate(request, response, response_body):
	'''
	Sets response content-encoding to 'deflate' and uses zlib compression to compress the
	response body.
	
	:param request: The current :mod:`frame.request.Request` object
	:param response: The current :mod:`frame.response.Response` object
	:param response_body: The response body
	:return: Compressed response_body
	'''
	
	if 'accept_encoding' in request.headers:
		if 'deflate' in request.headers.accept_encoding.split(','):
			response.headers['Content-Encoding'] = 'deflate'
			return zlib.compress(response_body)
	return response_body
