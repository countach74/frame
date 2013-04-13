'''
Frame is a simple Python web development framework that is aimed at bridging the
gap between the development and production environments. As such, one of the project's
main goals is to ensure that what you see when running the development HTTP server is
exactly what you'll see when running the application via FastCGI, which is the intended
deployment method.

Hello World
-----------
Creating your first Frame application is very easy! Check out this hello world::

	import frame
	
	# Create our root controller
	class Root(frame.Controller):
		def index(self):
			return 'Hello, world!'
			
	# Route it to a URI
	frame.routes.connect('/', 'root#index')
	
	# Start the development HTTP server
	frame.start_http()
	
... and that's it! And, unlike many other frameworks that get you out of the gate fast,
Frame's methodology facilitates creating very large applications as well.

The Basics
----------
Frame combines the Python Routes module and Jinja2 template engine to create a
comprehensive web developmeng framework. At this time, there isn't really a way to
change the dispatching to use something other than Routes, but this functionality may
be added in the future at some time. Also, just because it's assumed that you'll use
Jinja2, this is not required (although certain automated functionality will be lost).

Like many MVC-oriented frameworks, controllers in Frame contain a lot of central
information to the HTTP request and response. For example, :mod:`frame.request.Request`
and :mod:`frame.response.Response` are both available directly from within the
Controller. The goal is that most everything you'll need to interact with Frame
on a normal use-case are available from directly within the
:mod:`frame.controller.Controller`.
'''


import sys
from _app import app
from _routes import routes
from _config import config
from _logger import logger
from controller import Controller
from errors import *
from dotdict import DotDict
from pkg_resources import iter_entry_points


start_http = app.start_http
start_fcgi = app.start_fcgi


# Module registry
modules = DotDict()


# Load a module by name. Can specify keyword arguments that will be sent off to the
# module's entry point, if it's setup for them. :)
def load_module(name, *args, **kwargs):
	for entry_point in (i for i in iter_entry_points('frame.modules') if i.name == name):
		init = entry_point.load()
		result = init(app, *args, **kwargs)
		modules[entry_point.name] = result if result else sys.modules[init.__module__]