#!/usr/bin/python

import frame
from frame.util import MethodException


class Poo(frame.Controller):
  def crap(self):
    return {'name': 'Bob'}


class HelloWorld(frame.Controller):
  def index(self):
    return 'hello, world'

  def test(self):
    raise MethodException(Poo.crap)

  def other(self):
    return {'cool': 'stuff'}

  def throw_400(self):
    raise frame.Error400

  def throw_500(self):
    print wtf


frame.routes.connect('/', 'helloworld#index')
frame.routes.connect('/test', 'helloworld#test')
frame.routes.connect('/400', 'helloworld#throw_400')
frame.routes.connect('/500', 'helloworld#throw_500')
frame.routes.connect('/other', 'helloworld#other')


if __name__ == '__main__':
  frame.start_http('0.0.0.0')
