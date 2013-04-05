'''
All dispatcher plugins go here.
'''


class RoutesDispatcher(object):
  from _routes import routes
  
  def __init__(self, app):
    self.app = app
    
  def handle(self, *args, **kwargs):
    return self.app.routes.match(*args, **kwargs)