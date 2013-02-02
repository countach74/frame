from _dotdict import DotDict
from errors import HTTPError404
from cgi import parse_qs


class Response(object):
	def __init__(self, start_response, controller):
		self.__start_response = start_response

		if not controller:
			raise HTTPError404

		self.__controller = controller
		self.headers = DotDict({
			'Content-Type': 'text/html',
		})
		self.status = '200 OK'
			

	def render(self, query_string, uri_data):
		self.__start_response(self.status, self.headers.items())

		params = parse_qs(query_string)
		
		# Parse the params and convert to strings wherever list contains 1 item
		for key, value in params.items():
			if len(value) == 1:
				params[key] = value[0]

		return self.__controller(**dict(params.items() + uri_data.items()))
