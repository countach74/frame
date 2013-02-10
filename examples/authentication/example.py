#!/usr/bin/python

import frame
import auth
from controllers import *
import _routes


frame.app.session_interface.backend = 'Memcache'


if __name__ == '__main__':
	frame.start_http()
