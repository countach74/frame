from frame import app, connection
from frame.orm.datatypes import *


class Model(app.orm.Model):
	__connection__ = connection
	__database__ = 'test'


class User(Model):
	__collection__ = 'users'
	structure = {
		'username': StringType(charset='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
		'password': StringType(id='ok'),
		'email': EmailType(),
		'groups': ListType(choices={'users': 'Users', 'admin': 'Administrators'}),
	}

	required_fields = ['username', 'password', 'email']

	defaults = {'groups': ['users']}
