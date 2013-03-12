import threading
import sys
import time
import datetime
import os
from frame import logger


class ModuleMonitor(threading.Thread):
	'''
	Monitors all of the modules loaded by the current running application. If
	any of them change (detected via os.stat), reload the running process.
	'''
	def __init__(self, server, interval=1):
		self.server = server
		self.interval = interval
		self._stop = threading.Event()
		
		self.path = os.environ['_']

		threading.Thread.__init__(self)

	def run(self):
		logger.log_info("Starting module reloader...")
		datetime.datetime.now()
		last_scan = datetime.datetime.now()
		
		old_stats = self.stat_modules()

		while not self.stopped():
			now = datetime.datetime.now()
			delta = datetime.timedelta(seconds=self.interval)
			if now > last_scan + delta:
				new_stats = self.stat_modules()
				if not self.compare_stats(old_stats, new_stats):
					logger.log_info("File changed, reloading server...")
					self.server.stop()
					old_stats = new_stats
					args = ['python'] + list(sys.argv) + [os.environ]
					os.execle('/usr/bin/env', '', *args)
				old_stats = new_stats
			time.sleep(1)

	def stopped(self):
		return self._stop.is_set()

	def stop(self):
		logger.log_info("Stopping module reloader...")
		self._stop.set()
		
	def compare_stats(self, old, new):
		'''
		Returns true if the two stat dictionaries don't differ, false
		if they do.
		'''
		for key, value in old.items():
			if key in new and new[key] != value:
				return False
		return True
		
	def stat_modules(self):
		stats = {}
		for name, module in sys.modules.items():
			try:
				path = module.__file__
			except AttributeError:
				continue
			
			try:
				stats[path] = os.stat(path)
			except EnvironmentError:
				pass
			
			try:
				path = path[:-1]
				stats[path] = os.stat(path)
			except EnvironmentError:
				pass
			
		return stats
