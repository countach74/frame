#!/usr/bin/python

import frame


class HelloWorld(frame.Controller):
	def index(self):
		return "Hello, World!"


frame.routes.connect('/', 'helloworld#index')


if __name__ == '__main__':
	frame.start_http('0.0.0.0')
