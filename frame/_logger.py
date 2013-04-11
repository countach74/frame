'''
This module provides the logging interface for Frame. It is designed to be flexible and
extensible so that it can fit whatever needs you and your application have for logging.
If you don't like the log options, by all means, feel free to create your own by
subclassing :class:`Logger` and providing new :attr:`out` and :attr:`err` interfaces.

For example::

	import frame
	import frame._logger
	
	# Define configuration directives
	frame.config.logger.mysql = {'connection': None}

	class MysqlLogger(frame._logger.Logger):
		def __init__(self, connection):
			self.connection = connection
			
			class LogWriter(object):
				def __init__(self, table):
					self.table = table
					
				def write(self, message):
					# Handle write to database using self.table
					pass
					
			self.out = LogWriter('out')
			self.err = LogWriter('err')
			
	# Expose the logger to Frame
	frame._logger.MysqlLogger = MysqlLogger

Of course, our example doesn't really do anything, but hopefully that provides enough
information to get you started. It also may be a good idea to bypass the whole
:attr:`Logger.out` and :attr:`Logger.err` methodology and instead rewrite 
:meth:`Logger.log_message`. The choice is yours.

`Note:` The configuration directives are automatically passed to the logger's __init__
method.
'''


import sys
import datetime
from _config import config
from pytz import timezone
import os
from driverinterface import DriverInterface


class Logger(object):
	'''
	A mixin that provides basic logging API functionality.
	'''
	
	def populate_format_data(self, request, response, response_length):
		'''
		Gathers information about a request and its response and delivers a dictionary to be
		used to populate a log format string.
		
		:param request: The request's :mod:`frame.request.Request` object
		:param response: The request's :mod:`frame.response.Response` object
		:param response_length: The length (in bytes) of the response body
		:return: A format dictionary
		'''
		
		now = datetime.datetime.now()
		local_tz = timezone(config.timezone)
		
		dt_aware = local_tz.localize(now)
		
		timestamp = dt_aware.strftime("%d/%b/%Y:%H:%M:%S %z")
		
		try:
			status_code, status_message = response.status.split(None, 1)
		except ValueError:
			status_code = 'INVALID'
			status_message = 'INVALID'
			
		if 'user_agent' in request.headers:
			user_agent = request.headers.user_agent 
		else:
			user_agent = '-'
			
		if 'referer' in request.headers:
			referer = request.headers.referer
		else:
			referer = '-'
			
		headers = request.headers
		
		return {
			'remote_host': headers.remote_addr if 'remote_addr' in headers else '-',
			'timestamp': timestamp,
			'request_line': "%s %s %s" % (
				headers.request_method if 'request_method' in headers else '-',
				headers.request_uri if 'request_uri' in headers else '-',
				headers.server_protocol if 'server_protocol' in headers else '-'),
			'status_code': status_code,
			'body_size': response_length,
			'local_address': headers.server_addr if 'server_addr' in headers else '-',
			'environment': request.environ,
			'request_protocol': headers.server_protocol if 'server_protocol' in headers else '-',
			'request_method': headers.request_method if 'request_method' in headers else '-',
			'server_port': headers.server_port if 'server_port' in headers else '-',
			'query_string': headers.query_string if 'query_string' in headers else '-',
			'request_uri': headers.request_uri if 'request_uri' in headers else '-',
			'server_name': headers.server_name if 'server_name' in headers else '-',
			'user_agent': user_agent,
			'referer': referer
		}
		
	def log_request(self, request, response, response_length):
		'''
		Formats a request and sends it off to the :attr:`Logger.out` attribute.
		'''
		
		format_data = self.populate_format_data(request, response, response_length)
		
		self.out.write(
			"%(remote_host)s [%(timestamp)s] \"%(request_line)s\" %(status_code)s "
			"%(body_size)s \"%(referer)s\" \"%(user_agent)s\"\n" % format_data)
	
	def log_message(self, level, message):
		'''
		Send a message to the log interface
		
		:param level: Log level to used
		:param message: Message to send
		'''
		now = datetime.datetime.now()
		timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
		self.err.write("%s: [%s] %s\n" % (timestamp, level.upper(), message))
		
	def log_error(self, message):
		'''
		Sends an 'ERROR' message to the logger.
		
		:param message: Message to send
		'''
		self.log_message('ERROR', message)
		
	def log_info(self, message):
		'''
		Sends an 'INFO' message to the logger.
		
		:param message: Message to send
		'''
		self.log_message('INFO', message)
		
	def log_warning(self, message):
		'''
		Sends a 'WARNING' message to the logger.
		
		:param message: Message to send
		'''
		self.log_message('WARNING', message)
		
	def log_critical(self, message):
		'''
		Sends a 'CRITICAL' message to the logger.
		
		:param message: Message to send
		'''
		self.log_message('CRIT', message)
		
	def log_exception(self, message, raw=False):
		'''
		Sends a 'CRITICAL' message to the logger or write to :attr:`Logger.err` if :param raw:
		is passed as ``True``.
		
		:param message: Message to send
		:param raw: Whether or not to bypass the logger and send to :attr:`Logger.err`
			directly
		'''
		if not raw:
			self.log_critical(message)
		else:
			self.err.write("%s\n" % message.rstrip())

		
class StdoutLogger(Logger):
	'''
	A simple logger that by default assigns :attr:`out` and :attr:`err` to :attr:`sys.stdout`
	and :attr:`sys.stderr`, respectively. If redirection to a file is wanted instead, it is
	recommended that the ``config.logger.stdout.out`` and/or ``config.logger.stdout.err``
	directives be set to instances of :mod:`frame.util.FileLogger` instead.
	'''
	
	def __init__(self, out, err):
		self.out = out
		self.err = err
		
		
class NullLogger(Logger):
	'''
	A very bad logger! Use this if you want to completely disregard all output from the
	Frame application.
	'''
	
	def __init__(self):
		null = open(os.devnull, 'w')
		self.out = null
		self.err = null
		
		
class ProductionLogger(Logger):
	'''
	Designed originally to send Frame application output to the syslog facility, but
	frankly, sending to files is more typical. This will likely be deprecated shortly.
	'''
	
	def __init__(self, facility, out, err):
		import syslog
		self.syslog = syslog
		
		facility = getattr(self.syslog, 'LOG_%s' % facility.upper())
		self.syslog.openlog(config.application.name, 0, facility)
		self.out = out
		self.err = err
		
	'''
	@property
	def out(self):
		
		class WriteOut(object):
			def __init__(self, logger):
				self.logger = logger
				
			def write(self, data):
				self.logger.log_info(data.rstrip())
			
		return WriteOut(self)
	'''
	
	def log_message(self, level, message):
		priority = getattr(self.syslog, 'LOG_%s' % level.upper())
		self.syslog.syslog(priority, message)
		
		
class LogInterface(DriverInterface):
	def __init__(self, *args, **kwargs):
		DriverInterface.__init__(self, *args, **kwargs)
		
		self.update({
			'stdout': StdoutLogger,
			'null': NullLogger,
			'production': ProductionLogger
		})
		
		self.logger = None
		
	def __getattr__(self, key):
		if key.startswith('log_'):
			self.load_current()
			return getattr(self.logger, key)
		else:
			raise AttributeError(key)
			
	def init(self, driver):
		if not self.logger:
			options = self.config[self.config.driver]
			self.logger = driver(**options)
		return self.logger
		
		
logger = LogInterface(None, config=config.logger)