class HTTPError(Exception):
	pass


class HTTPError404(HTTPError):
	def __init__(self):
		self.status = "404 Not Found"
		self.body = "<h3>Oops! File not found!</h3>"
		self.headers = [('Content-Type', 'text/html')]
