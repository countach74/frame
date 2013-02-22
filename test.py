#!/usr/bin/python

import frame
from frame.orm.datatypes import SubmitType

frame.connection = frame.app.Connection()

from models import *


class Root(frame.Controller):
	def index(self):
		pass


class Users(frame.Controller):
	def index(self):
		users = User.find()
		return {'users': users}

	def show(self, slug):
		user = User.find_one({'username': slug})
		if user:
			return {'user': user}

	def new(self):
		submit_button = SubmitType("Submit", {'class': 'stuff'})
		return {'model': User, 'buttons': [submit_button]}

	def create(self, **data):
		user = User(data)
		user.save()
		self.redirect('/users')


class Friends(frame.Controller):
	def index(self, user):
		return "Friends list here for friend: %s" % user

	def show(self, user, slug):
		return {} #"Show friend %s for user %s" % (slug, user)


frame.routes.connect('/', 'root#index')
frame.routes.resource('users')
frame.routes.resource('friends', '/users/{user}/friends')


if __name__ == '__main__':
	frame.start_http()
