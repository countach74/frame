'''
Defines all of the Frame exception types. Anything derrived from HTTPError is expected
to be some sort of HTTPError (301, 404, 500, etc). Under the current implementation,
overriding the default behavior of these errors is difficult (but not impossible). However,
modifying the template for the errors is very simple. See
:ref:`overriding-error-templates` for more information on customizing the various error
messages.
'''


import sys, os
from cgi import escape
from _logger import logger
from _config import config
from dotdict import DotDict


_default_error_headers = dict(config.response.default_headers)
_default_error_headers.update({
	'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
	'Pragma': 'no-cache'
})


class HTTPError(Exception):
	'''
	The main HTTP error class; anything that derives from this exception class is handled
	specially by Frame. These exceptions are really built halfway like a response and in
	fact include a fake response object so that they can be passed off to be rendered
	as if they are in fact, a response.
	
	`Note`: :exc:`HTTPError` exceptions and derivates default with headers to prevent
	caching. Specifically, the following is set::
	
		headers = {
			'Content-Type': 'text/html',
			'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
			'Pragma': 'no-cache'
		}
	'''
	
	response_class = None
	
	def __init__(self, status, headers={}, *args, **kwargs):
		'''
		Initialize the HTTP Error.
		
		:param status: The status line to send the WSGI server
		:param headers: Headers to apply to the error
		'''
		
		base_headers = DotDict(_default_error_headers)
		base_headers.update(headers)
		
		#: Stores any extra positional arguments; not actually used as of now
		self.args = args
		
		#: Stores any keyword arguments; these are passed to the template when rendered
		self.kwargs = kwargs
		
		#: A fake response object that stores the status line and headers
		self.response = self.response_class.from_data(status, base_headers, None)
		
	def render(self, app):
		'''
		Renders the error template, which is assumed to be in the template directory at
		``errors/{error_code}.html``.
		
		:param app: The Frame application
		:return: The rendered error
		'''
		
		status_code = self.response.status.split(None, 1)[0]
		template_path = 'errors/%s.html' % status_code
		
		self.response.body = app.environment.get_template(template_path).render(
			app=app, status=self.response.status, **self.kwargs)
			
			
class Error301(HTTPError):
	'''
	A simple 301 redirect. Note that the 3xx errors assume they will be used as redirects
	and actually receive different initialization arguments than the other errorrs.
	'''
	
	def __init__(self, url, status='301 Moved Permanently', *args, **kwargs):
		'''
		Initialize the error.
		
		:param url: The URL to redirect to
		:param status: The status line to use
		'''
		
		headers = {'Location': url}
		HTTPError.__init__(status, headers, *args, **kwargs)
			
			
class Error302(HTTPError):
	'''
	Like :exc:`Error301` but with ``302 Found`` status instead.
	'''
	def __init__(self, url, status='302 Found', *args, **kwargs):
		headers = {'Location': url}
		HTTPError.__init__(status, headers, *args, **kwargs)
		
		
class Error303(Error301):
	pass
		
		
class Error404(HTTPError):
	'''
	Your generic 404 Not Found error. An unmodified :exc:`HTTPError` with the exception of
	the status line being changed to ``404 Not Found``.
	'''
	def __init__(self, status='404 Not Found', *args, **kwargs):
		HTTPError.__init__(self, status, *args, **kwargs)
		
		
class Error401(HTTPError):
	'''
	Your generic 404 Not Authorized error. An unmodified :exc:`HTTPError` with the exception of
	the status line being changed to ``401 Not Authorized``.
	'''
	def __init__(self, status='401 Not Authorized', *args, **kwargs):
		HTTPError.__init__(self, status, *args, **kwargs)
		
		
class Error403(HTTPError):
	'''
	Your generic 403 Forbidden error. An unmodified :exc:`HTTPError` with the exception of
	the status line being changed to ``403 Forbidden``.
	'''
	def __init__(self, status='403 Forbidden', *args, **kwargs):
		HTTPError.__init__(self, status, *args, **kwargs)
		
		
class Error500(HTTPError):
	'''
	You guessed it: Internal Server Error! This exception does things a little bit
	different in that it actually renders out the exception traceback.
	'''
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
	'''
	Session failed to load.
	'''
	pass


class SessionSaveError(Exception):
	'''
	Session failed to save.
	'''
	pass
