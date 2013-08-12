#!/usr/bin/python

import frame
from frame.util import MethodException
import sys


class HelloWorld(frame.Controller):
  def index(self):
    print 'index()'
    self.response.headers['Content-Type'] = 'text/plain'
    return 'hello, world'

  def other(self):
    return {'name': 'Bob'}

  def throw_400(self):
    raise frame.Error400

  def throw_500(self):
    try:
      print crap
    except Exception, e:
      pass
    raise frame.Error500

  def _redirect(self):
    self.redirect('/')


frame.routes.connect('/', 'helloworld#index')
frame.routes.connect('/400', 'helloworld#throw_400')
frame.routes.connect('/500', 'helloworld#throw_500')
frame.routes.connect('/other', 'helloworld#other')
frame.routes.connect('/redirect', 'helloworld#_redirect')


if __name__ == '__main__':
  frame.start_http('0.0.0.0')
