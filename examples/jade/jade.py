import frame


frame.config.templates.driver = 'jade'
frame.config.templates.suffix = '.jade'


class Root(frame.Controller):
  def index(self):
    pass


frame.routes.connect('/', 'root#index')


if __name__ == '__main__':
  frame.start_http()
