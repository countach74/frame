'''
Defines all of the Frame exception types. Anything derrived from HTTPError is expected
to be some sort of HTTPError (301, 404, 500, etc). Under the current implementation,
overriding the default behavior of these errors is difficult (but not impossible). However,
modifying the template for the errors is very simple. See
:ref:`overriding-error-templates`
'''


import sys, os
from cgi import escape
from _logger import logger
from dotdict import DotDict


_default_error_headers = {
	'Content-Type': 'text/html',
	'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
	'Pragma': 'no-cache'
}


class HTTPError(Exception):
	def __init__(self, status, headers={}, *args, **kwargs):
		base_headers = DotDict(_default_error_headers)
		base_headers.update(headers)
			
		self.args = args
		self.kwargs = kwargs
		
		self.response = DotDict({
			'status': status,
			'headers': base_headers
		})
		
	def render(self, app):
		app.response = self.response
		status_code = self.response.status.split(None, 1)[0]
		template_path = 'errors/%s.html' % status_code
		
		return app.environment.get_template(template_path).render(
			app=app, status=self.response.status, **self.kwargs)
			
			
class Error301(HTTPError):
	def __init__(self, url, status='301 Moved Permanently', *args, **kwargs):
		headers = {'Location': url}
		HTTPError.__init__(status, headers, *args, **kwargs)
			
			
class Error302(HTTPError):
	def __init__(self, url, status='302 Found', *args, **kwargs):
		headers = {'Location': url}
		HTTPError.__init__(status, headers, *args, **kwargs)
		
		
class Error303(Error301):
	pass
		
		
class Error404(HTTPError):
	def __init__(self, status='404 File Not Found', *args, **kwargs):
		HTTPError.__init__(self, status, *args, **kwargs)
		
		
class Error401(HTTPError):
	def __init__(self, status='401 Not Authorized', *args, **kwargs):
		HTTPError.__init__(self, status, *args, **kwargs)
		
		
class Error403(HTTPError):
	def __init__(self, status='403 Forbidden', *args, **kwargs):
		HTTPError.__init__(self, status, *args, **kwargs)
		
		
class Error500(HTTPError):
	def __init__(self, status='500 Internal Server Error', *args, **kwargs):
		import traceback
		new_kwargs = dict(kwargs)
		
		e_type, e_value, e_tb = sys.exc_info()
		if e_tb:
			tb = traceback.format_exception(e_type, e_value, e_tb)
			new_kwargs['traceback'] = map(escape, tb)
			for line in tb:
				logger.log_exception(line, True)
		else:
			new_kwargs['traceback'] = None
			
		HTTPError.__init__(self, status, *args, **new_kwargs)


class SessionLoadError(Exception):
	pass


class SessionSaveError(Exception):
	pass
