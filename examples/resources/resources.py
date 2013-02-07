#!/usr/bin/python

import frame
from frame.postprocessors import deflate


# Import all of the controllers defined in 'controllers' directory
from controllers import *

# Apply zlib compression to responses
frame.app.post_processors.append(deflate)


frame.routes.connect('/', 'users#index')

# Apply resource URI routing to 'Users' controller
frame.routes.resource('users')


if __name__ == '__main__':
	frame.start_fcgi()
