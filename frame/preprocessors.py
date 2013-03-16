'''
Pre processors allow interaction with the request and response objects before they get
to the controller. This is actually how form decoding is handled. A pre processor is
a simple callable that is passed the current request and response objects. While a pre
processor does not return any value, it can make changes to both of these objects. One
thing in particular that may be of interest is the ability to modify the
:attr:`frame.response.Response.additional_params` dictionary to pass additional keyword
parameters to the controller action method.
'''


from util import parse_query_string
from cgi import FieldStorage
import json


def form_url_decoder(request, response):
	'''
	Decodes standard URL encoded form data and passes the attributes off to the controller
	action method as keyword arguments.
	'''
	
	if 'content_type' in request.headers:
		if request.headers.content_type.lower() == 'application/x-www-form-urlencoded':
			params = parse_query_string(request.body)
			for key, value in params.items():
				response.additional_params[key] = value


def form_json_decoder(request, response):
	'''
	Decodes JSON encoded form data and passes the object attributes off to the controller
	action method as keyword arguments.
	'''
	
	if 'content_type' in request.headers:
		if request.headers.content_type.lower() == 'application/json':
			try:
				params = json.loads(request.body)
			except ValueError:
				return
			else:
				for key, value in params.items():
					response.additional_params[key] = value


def form_multipart_decoder(request, response):
	'''
	Exactly like :func:`form_url_decoder` except that file uploads are handled via
	:mod:`cgi.FieldStorage`, which presents file uploads as file-like objects.
	'''
	
	if 'content_type' in request.headers:
		if request.headers.content_type.lower().startswith('multipart/form-data'):
			fs = FieldStorage(fp=request.wsgi.input, environ=request.environ)
			for i in fs:
				if isinstance(fs[i], list):
					data = []
					for j in fs[i]:
						if j.type == 'text/plain':
							data.append(j.file.read())
						else:
							data.append(j)
					response.additional_params[i] = data
				else:
					if fs[i].type == 'text/plain':
						response.additional_params[i] = fs[i].file.read()
					else:
						response.additional_params[i] = fs[i]
						
		
def handle_query_string(request, response):
	if 'query_string' in request.headers:
		response.additional_params.update(parse_query_string(request.headers.query_string))