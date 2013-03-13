from dotdict import DotDict
from errors import Error404
from util import parse_query_string
import datetime
from _routes import routes
from _config import config
import os
from util import format_date, get_gmt_now


class Response(object):
	'''
	The :class:`Response` class stores a collection of data about the HTTP response. It is
	used by the :class:`frame._app.App` to deliver information to the client. The current
	:class:`Response` object provides interfaces to:
	
	* Cookie creation and deletion
	* Set response status line and headers
	* Append keyword arguments to the controller action method that is called
	
	'''
	
	def __init__(self, app, controller):
		if not controller:
			raise Error404

		#: The Frame application
		self.app = app
		
		#: The current controller action method (mislabeled)
		self.controller = controller
		
		#: A :mod:`frame.dotdict.DotDict` that stores the response headers
		self.headers = DotDict(config.response.default_headers)
		self.headers.update({
			'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0',
			'Pragma': 'no-cache'
		})
		self.status = '200 OK'
		
		#: Additional keyword arguments to pass off to the controller action method
		#: when it is called
		self.additional_params = {}
			
	def set_cookie(self, key, value, expires=1, domain=None, path='/', secure=False, http_only=False):
		'''
		Send a cookie to the client.
		
		:param key: Key to use for cookie
		:param value: Data to pass to cookie
		:param expires: How long (in hours) until the cookie expires
		:param domain: Domain that the cookie should apply to
		:param path: Path that the cookie should apply to
		:param secure: Whether or not "Secure" flag should be passed to cookie
		:param http_only: Whether or not "HttpOnly" flag should be passed to cookie
		'''
		
		cookie = ["%s=%s" % (key, value)]

		if expires:
			now = get_gmt_now()
			then = now + datetime.timedelta(hours=expires)
			cookie.append("Expires=%s" % format_date(then))
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
		'''
		A helper function to expire a cookie and change its value to 'deleted' (just in case
		for some reason it isn't expired).
		
		:param key: The key of the cookie to expire
		'''
		self.headers['Set-Cookie'] = "%s=deleted; Expires=Thu, Jan 01 1970 00:00:00 GMT" % key

	def start_response(self):
		'''
		Starts the WSGI response back to the server. Sends the status line and a list of
		header tuples.
		
		.. deprecated:: 0.1
		   Handled by Frame application instead.
		'''
		self._start_response(self.status, self.headers.items())

	def render(self, query_string, uri_data):
		'''
		Calls the controller action with the parameters passed via the query string, uri_data
		dictionary, and additional_params dictionary.
		
		:param query_string: The query string from the WSGI environ dictionary
		:param uri_data: Parameters passed via routes. For example, consider the route
			``/users/{user}``; when the client enters ``/users/bob``, uri_data will be passed
			``user='bob'``
		:return: Rendered response body
		'''
		
		params = parse_query_string(query_string)

		# Must render the page before we send start_response; otherwise, controller-set
		# headers will not get set in time.
		result = self.controller(**dict(
			params.items() +
			uri_data.items() +
			self.additional_params.items()))
		
		if result is None or isinstance(result, dict):
			method_name = self.controller.__name__
			
			if hasattr(self.controller.im_self, '__resource__'):
				template_dir = self.controller.im_self.__resource__['template_dir']
				template_path = os.path.join(template_dir, method_name + '.html')
			
				result = self.controller.im_self.get_template(template_path).render(
					result if result else {})
					
			else:
				template_dir = self.controller.im_self.__class__.__name__.lower()
				template_path = os.path.join(template_dir, method_name + '.html')
				
				result = self.controller.im_self.get_template(template_path).render(
					result if result else {})

		return result
