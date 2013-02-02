import threading
import sys
import hashlib
import time
import datetime
import os


class ModuleMonitor(threading.Thread):
	def __init__(self, server, hash_algorithm=hashlib.sha1, interval=1):
		self.server = server
		self.hash_algorithm = hash_algorithm
		self.interval = interval
		self._stop = threading.Event()

		threading.Thread.__init__(self)

	def run(self):
		datetime.datetime.now()
		initial_hashes = self.hash_modules()
		last_scan = datetime.datetime.now()

		while not self.stopped():
			now = datetime.datetime.now()
			delta = datetime.timedelta(seconds=self.interval)
			if now > last_scan + delta:
				module_hashes = self.hash_modules()
				if initial_hashes != module_hashes:
					initial_hashes = module_hashes
			time.sleep(1)

	def stopped(self):
		return self._stop.is_set()

	def stop(self):
		self._stop.set()

	def hash_modules(self):
		mod_hash = self.hash_algorithm()
		for value in sorted(sys.modules.values()):
			if not value or not hasattr(value, '__file__'):
				continue

			mod_path = value.__file__
			crud, extension = os.path.splitext(mod_path)
			if extension == '.pyc':
				source_path = mod_path[0:-1]
			else:
				continue

			if not os.path.exists(source_path):
				continue

			with open(source_path, 'r') as f:
				data = f.read(1024)
				while data:
					mod_hash.update(data)
					data = f.read(1024)

		return mod_hash.hexdigest()
