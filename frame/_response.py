from _dotdict import DotDict
from errors import HTTPError404
from util import parse_query_string
import datetime


class Response(object):
	def __init__(self, controller):
		if not controller:
			raise HTTPError404

		self._controller = controller
		self.headers = DotDict({
			'Content-Type': 'text/html',
		})
		self.status = '200 OK'
		self.additional_params = {}
			
	def set_cookie(self, key, value, expires=1, domain=None, path='/', secure=False, http_only=False):
		cookie = ["%s=%s" % (key, value)]

		if expires:
			now = datetime.datetime.utcnow()
			then = now + datetime.timedelta(hours=expires)
			cookie.append("Expires=%s" % then.strftime("%a, %d-%b-%Y %H:%M:%S UTC"))
		if domain:
			cookie.append("Domain=%s" % domain)
		if path:
			cookie.append("Path=%s" % path)
		if secure:
			cookie.append("Secure")
		if http_only:
			cookie.append("HttpOnly")

		self.headers['Set-Cookie'] = '; '.join(cookie)

	def delete_cookie(self, key):
		self.headers['Set-Cookie'] = "%s=deleted; Expires=Thu, Jan 01 1970 00:00:00 GMT" % key

	def start_response(self):
		self._start_response(self.status, self.headers.items())

	def render(self, query_string, uri_data):
		params = parse_query_string(query_string)

		# Must render the page before we send start_response; otherwise, controller-set
		# headers will not get set in time.
		result = self._controller(**dict(
			params.items() +
			uri_data.items() +
			self.additional_params.items()))

		return result
