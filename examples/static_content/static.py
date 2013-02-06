#!/usr/bin/python

import frame


class Root(frame.Controller):
	def index(self):
		return self.get_template("root/index.html").render()


frame.routes.connect('/', 'root#index')


if __name__ == '__main__':
	frame.start_http()
