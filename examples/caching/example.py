#!/usr/bin/python

import frame
import time
from frame.caching import *


class Root(frame.Controller):
	def index(self):
		return self.get_template('index.html').render(title='Hello World!')


frame.routes.connect('/', 'root#index')


if __name__ == '__main__':
	frame.start_fcgi()
