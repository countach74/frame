from util import parse_query_string
import json


def form_url_encoder(request, response):
	if 'content_type' in request.headers:
		if request.headers.content_type.lower() == 'application/x-www-form-urlencoded':
			params = parse_query_string(request.body)
			for key, value in params.items():
				response.additional_params[key] = value


def form_ajax(request, response):
	if 'content_type' in request.headers:
		if request.headers.content_type.lower() == 'application/json':
			try:
				params = json.loads(request.body)
			except ValueError:
				return
			else:
				for key, value in params.items():
					response.additional_params[key] = value
