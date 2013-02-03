#!/usr/bin/python

from flup.server.fcgi import WSGIServer
import frame
from frame.controller import Controller
import threading

class Root(Controller):
	def index(self):
		return self.get_template('root/index.html').render(session=self.session)

	def broken(self):
		return poo

	def increase(self):
		if 'num_visits' in self.session:
			self.session['num_visits'] += 1
		else:
			self.session['num_visits'] = 1

	def get_visits(self):
		return self.session['num_visits']

	def test(self, name, **kwargs):
		response = ["Hmm, I don't know about this. %s" % name]
		for k, v in kwargs.items():
			response.append("<div>%s: %s</div>" % (k, v))

		return ''.join(response)


class Messages(Controller):
	def index(self, content_type='html'):
		return "Messages go here. %s" % content_type

	def show(self, slug, content_type='html'):
		return "Slug: %s, format: %s" % (slug, content_type)


frame.routes.connect("/", controller="root#index")
frame.routes.connect("/broken", controller="root#broken")
frame.routes.connect("/increase", controller="root#increase")
frame.routes.connect("/get_visits", controller="root#get_visits")
frame.routes.resource('messages')

frame.app.debug = True

frame.start_fcgi()
#frame.start_http()
