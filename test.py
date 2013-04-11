#!/usr/bin/python

import frame
from frame.util import FileLogger
from wsgiref.simple_server import make_server

class Root(frame.Controller):
	def index(self):
		if 'visits' not in self.session:
			self.session['visits'] = 1
		else:
			self.session['visits'] += 1
		return 'home page! Visits: %s' % self.session['visits']
	
	def bad_request(self):
		return asdfasdf


def remove_hop_by_hop(request, response):
	bad_headers = ('Connection', 'Transfer-Encoding')
	for header in bad_headers:
		if header in response.headers:
			del(response.headers[header])

frame.routes.expose('root', '/')

if __name__ == '__main__':
	frame.app.start_http()
