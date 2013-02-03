import zlib


def gzip(request, headers, response_body):
	if 'accept_encoding' in request.headers:
		if 'deflate' in request.headers.accept_encoding.split(','):
			headers['Content-Encoding'] = 'deflate'
			return (headers, zlib.compress(response_body))
	return (headers, response_body)
