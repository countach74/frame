#!/usr/bin/python

import frame


class Root(frame.Controller):
	def save(self, name='bob'):
		if 'name' not in self.session:
			self.session['name'] = name

	def get(self):
		try:
			return "Name: %s" % self.session['name']
		except KeyError:
			return "No name saved."


frame.routes.connect('/', 'root#get')
frame.routes.connect('/save/{name}', 'root#save')

#frame.app.session_interface.backend = 'Memcache'


if __name__ == '__main__':
	frame.start_fcgi()
