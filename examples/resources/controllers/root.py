from frame import Controller


class Root(Controller):
	def index(self):
		return self.get_template('root/index.html').render()
