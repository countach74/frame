from util import parse_query_string
from cgi import FieldStorage
import json


def form_url_encoder(request, response):
	if 'content_type' in request.headers:
		if request.headers.content_type.lower() == 'application/x-www-form-urlencoded':
			params = parse_query_string(request.body)
			for key, value in params.items():
				response.additional_params[key] = value


def form_json_encoder(request, response):
	if 'content_type' in request.headers:
		if request.headers.content_type.lower() == 'application/json':
			try:
				params = json.loads(request.body)
			except ValueError:
				return
			else:
				for key, value in params.items():
					response.additional_params[key] = value


def form_multipart_encoder(request, response):
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