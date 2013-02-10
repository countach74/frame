import frame


class Admin(frame.Controller):
	@frame.Auth
	def index(self):
		return "Hello, admin"
