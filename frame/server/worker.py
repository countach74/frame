import threading
from frame._config import config

try:
	from Queue import Queue
except ImportError:
	from queue import Queue


class HTTPWorker(threading.Thread):
	def __init__(self, queue):
		self.queue = queue
		threading.Thread.__init__(self)
		
	def run(self):
		while True:
			item = self.queue.get()
			if not item:
				break
			else:
				connection, request = item
				connection.handle_request(request)
				self.queue.task_done()
		self.queue.task_done()
		
	
class HTTPQueue(object):
	def __init__(self, server, num_workers=10):
		self.server = server
		self.num_workers = num_workers
		
		self.queue = Queue()
		self.workers = self.start_workers(num_workers)
		
	def start_workers(self, num_workers):
		workers = []
		
		for w in xrange(num_workers):
			worker = HTTPWorker(self.queue)
			workers.append(worker)
			worker.start()
			
		return workers
		
	def stop(self):
		for w in self.workers:
			self.queue.put(None)
		self.queue.join()
		
	def put(self, *args):
		self.queue.put(args)