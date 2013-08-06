from frame import Controller


class Root(Controller):
  def index(self):
    # Returning nothing is the same thing as returning an empty dict, which by
    # default returns the rendered template at
    # '{lowercase_controller_name}/{method}.html'. Basically, by 'passing',
    # the following is done internally:
    #   return self.get_template('root/index.html').render()
    pass
