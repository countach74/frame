import frame


class Root(frame.Controller):
	def index(self):
		return "Hello, world"

	def login(self):
		return "You need to login"
