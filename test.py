#!/usr/bin/python

import frame
from frame.controller import Controller
import threading

class Root(Controller):
	def index(self):
		return self.get_template('root/index.html').render()

	def poo(self):
		return "Oh boy. %s" % self.request.headers.cookie

	def test(self, name, **kwargs):
		response = ["Hmm, I don't know about this. %s" % name]
		for k, v in kwargs.items():
			response.append("<div>%s: %s</div>" % (k, v))

		return ''.join(response)

frame.routes.connect("/", controller="root#index")
frame.routes.connect("/test/{name}", controller="root#test")
frame.routes.connect("/poo", controller="root#poo")

frame.app.debug = True

#app.start_fcgi()
frame.app.start_http()
