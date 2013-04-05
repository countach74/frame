#!/usr/bin/python

import frame

class Root(frame.Controller):
	def index(self):
		return 'home page!'
	
	def bad_request(self):
		return asdfasdf

frame.routes.connect('/', 'root#index')

if __name__ == '__main__':
	frame.start_http()
