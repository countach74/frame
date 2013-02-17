#!/usr/bin/python

import frame
from frame.orm.datatypes import SubmitType

frame.connection = frame.app.Connection()

from models import *


class Root(frame.Controller):
	def index(self):
		return "Hi. It might work"


class Users(frame.Controller):
	def index(self):
		users = User.find()
		return self.get_template('users/index.html').render(users=users)

	def show(self, slug):
		user = User.find_one({'username': slug})
		if user:
			return self.get_template('users/show.html').render(user=user)

	def new(self):
		submit_button = SubmitType("Submit", {'class': 'stuff'})
		return self.get_template('users/new.html').render(model=User, buttons=[submit_button])

	def create(self, **data):
		user = User(data)
		user.save()
		self.redirect('/users')


frame.routes.connect('/', 'root#index')
frame.routes.resource('users')


if __name__ == '__main__':
	frame.start_http()
