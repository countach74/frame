#!/usr/bin/python

import frame
from frame.util import FileLogger
from wsgiref.simple_server import make_server
from frame.staticgenerator import StaticGenerator

users = [
	{'username': 'bob'},
	{'username': 'hillary'}
]

class Root(frame.Controller):
	def index(self):
		if 'visits' not in self.session:
			self.session['visits'] = 1
		else:
			self.session['visits'] += 1
		return 'home page! Visits: %s' % self.session['visits']
	
	def bad_request(self):
		return asdfasdf


class Users(frame.Controller):
	def index(self):
		return {'users': users}

	def show(self, slug):
		return 'user %s' % slug


class Moderators(frame.Controller):
	def index(self):
		return {'users': users}

	def show(self, slug):
		return 'moderator %s' % slug


class Friends(frame.Controller):
	def index(self, user):
		return {'user': user}

	def show(self, user, slug):
		return {'user': user, 'friend': slug}


def remove_hop_by_hop(request, response):
	bad_headers = ('Connection', 'Transfer-Encoding')
	for header in bad_headers:
		if header in response.headers:
			del(response.headers[header])


frame.routes.expose('root', '/')
frame.routes.resource('users')
frame.routes.resource('moderators')
frame.routes.resource('friends', '/users/{user}/friends')
frame.routes.resource('friends', '/moderators/{user}/friends')


if __name__ == '__main__':
	sg = StaticGenerator(frame.app, '/home/countach74/blackpulp/staticsite')

	static_paths = (
		'/',
		'/users/bob',
		'/users/bob/friends/jo'
	)

	map(lambda x: x.save(), sg.generate(static_paths))
