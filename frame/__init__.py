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

10,000 Feet
-----------
Most everything in Frame is all centered around the :mod:`frame._app.App`, which is a :mod:`frame.util.Singleton`
instantiated at at :mod:`frame.app`

'''


from _app import app
from _routes import routes
from _config import config
from _logger import logger
from controller import Controller
from errors import Error301, Error302, Error303, Error404, Error500


start_http = app.start_http
start_fcgi = app.start_fcgi