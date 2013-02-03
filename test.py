#!/usr/bin/python

from flup.server.fcgi import WSGIServer
import frame
import frame.postprocessors
from frame.controller import Controller
import threading

class Root(Controller):
	def index(self):
		return self.get_template('root/index.html').render(session=self.session)

	def get_headers(self):
		response = []
		for k, v in self.request.headers.items():
			response.append("<div>%s: %s</div>" % (k, v))
		return '\n'.join(response)

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
frame.routes.connect("/get_headers", controller="root#get_headers")
frame.routes.resource('messages')

frame.app.post_processors.append(frame.postprocessors.gzip)
frame.app.session_interface.backend = 'Memory'

frame.start_fcgi()
#frame.start_http()
