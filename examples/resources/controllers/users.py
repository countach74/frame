from frame import Controller


class Users(Controller):
	def __init__(self):
		Controller.__init__(self)
	
		self.users = {
			'bob': {'name': 'bob', 'email': 'bob@email.com'},
			'joe': {'name': 'joe', 'email': 'joe@joeemail.com'}
		}

	def index(self):
		users = self.users.values()

		return self.get_template('users/index.html').render(users=users)

	def show(self, slug):
		try:
			user = self.users[slug]
		except KeyError:
			raise Error404("Cannot find that user")
		else:
			return self.get_template('users/show.html').render(user=user)

	def new(self):
		return self.get_template('users/new.html').render()

	def create(self, name, email):
		if name not in self.users:
			self.users[name] = {'name': name, 'email': email}
			self.redirect('/users')

		else:
			return self.get_template('users/taken.html').render()
