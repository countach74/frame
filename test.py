#!/usr/bin/python

import frame

class Root(frame.Controller):
	def index(self):
		if 'visits' not in self.session:
			self.session['visits'] = 1
		else:
			self.session['visits'] += 1
		return 'home page! Visits: %s' % self.session['visits']
	
	def bad_request(self):
		return asdfasdf

frame.routes.expose('root', '/')

frame.config.static_map['/passwd'] = '/etc/passwd'

if __name__ == '__main__':
	frame.start_http()
