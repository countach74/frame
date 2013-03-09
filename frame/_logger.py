import sys
import datetime
from _config import config
from pytz import timezone
import os


class Logger(object):
	def populate_format_data(self, request, status, headers, response_length):
		now = datetime.datetime.now()
		local_tz = timezone(config.timezone)
		
		dt_aware = local_tz.localize(now)
		
		timestamp = dt_aware.strftime("%d/%b/%Y:%H:%M:%S %z")
		
		try:
			status_code, status_message = status.split(None, 1)
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
		
	def log_request(self, request, status, headers, response_length):
		format_data = self.populate_format_data(request, status, headers, response_length)
		
		self.out.write(
			"%(remote_host)s [%(timestamp)s] \"%(request_line)s\" %(status_code)s "
			"%(body_size)s \"%(referer)s\" \"%(user_agent)s\"\n" % format_data)
	
	def log_message(self, level, message):
		now = datetime.datetime.now()
		timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
		self.err.write("%s: [%s] %s\n" % (timestamp, level.upper(), message))
		
	def log_error(self, message):
		self.log_message('ERROR', message)
		
	def log_info(self, message):
		self.log_message('INFO', message)
		
	def log_warning(self, message):
		self.log_message('WARNING', message)
		
	def log_critical(self, message):
		self.log_message('CRIT', message)
		
	def log_exception(self, message, raw=False):
		if not raw:
			self.log_critical(message)
		else:
			self.err.write("%s\n" % message.rstrip())

		
class StdoutLogger(Logger):
	def __init__(self, out, err):
		self.out = out
		self.err = err
		
		
class NullLogger(Logger):
	def __init__(self):
		null = open(os.devnull, 'w')
		self.out = null
		self.err = null
		
		
class ProductionLogger(Logger):
	import syslog
	
	def __init__(self, facility, out, err):
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
		
		
class LogInterface(object):
	def __init__(self):
		self.logger = None
		
	def setup_logger(self):
		if not self.logger:
			driver = config.logger.driver
			options = config.logger[driver]
			self.logger = globals()[driver.title() + 'Logger'](**options)
			
	def __getattr__(self, key):
		if key.startswith('log_'):
			self.setup_logger()
			attr = getattr(self.logger, key)
			return attr
		else:
			return object.__getattr__(self, key)
	

logger = LogInterface()