#!/usr/bin/python

from frame.server.http import HTTPServer
from flask import Flask


def app(environ, start_response):
	start_response('200 OK', [('Content-Type', 'text/html')])
	for k, v in environ.items():
		yield "<div>%s: %s</div>" % (k, v)


'''
app2 = Flask("boo")

class Root(object):
	def index(self):
		return "This is the root page"


root = Root()

app2.add_url_rule('/', 'index', root.index)
'''


if __name__ == '__main__':
	server = HTTPServer(app)
	server.start()
