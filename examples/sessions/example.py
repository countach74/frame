#!/usr/bin/python

import frame


class Root(frame.Controller):
	def save(self, name='bob'):
		self.session['name'] = name
		return 'name saved: %s' % name

	def get(self):
		try:
			return "Name: %s" % self.session['name']
		except KeyError:
			return "No name saved."


frame.routes.connect('/', 'root#get')
frame.routes.connect('/save/{name}', 'root#save')


if __name__ == '__main__':
	frame.start_http()
