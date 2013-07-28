import frame
from frame.controller import Controller


class Users(Controller):
	def __init__(self):
		Controller.__init__(self)
	
		self.users = {
			'bob': {'name': 'bob', 'email': 'bob@email.com'},
			'joe': {'name': 'joe', 'email': 'joe@joeemail.com'}
		}

	def index(self):
		users = self.users.values()
    return {'users': users}

	def show(self, slug):
		try:
			user = self.users[slug]
		except KeyError:
			raise frame.Error404("Cannot find that user")
		else:
      return {'user': user}

	def new(self):
		return self.get_template('users/new.html').render()

	def create(self, name, email):
		if name not in self.users:
			self.users[name] = {'name': name, 'email': email}
			self.redirect('/users', True)

		else:
			return self.get_template('users/taken.html').render()

	def delete(self, slug):
		if slug in self.users:
			del(self.users[slug])
    return 'User deleted'
