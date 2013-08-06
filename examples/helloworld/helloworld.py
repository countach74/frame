#!/usr/bin/python

import frame


class HelloWorld(frame.Controller):
  def index(self):
    return 'hello, world'

  def throw_400(self):
    raise frame.Error400


frame.routes.connect('/', 'helloworld#index')
frame.routes.connect('/400', 'helloworld#throw_400')


if __name__ == '__main__':
  frame.start_http('0.0.0.0')
