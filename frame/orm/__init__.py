import os
import sys
import stat
from importlib import import_module
from datatypes import *


available_drivers = {}
active_driver = 'mongo'

__dirname = os.path.dirname(os.path.abspath(__file__))

sys.path.append(__dirname)

# Populate available_drivers
for i in os.listdir(os.path.join(__dirname, 'drivers')):
	st = os.stat(os.path.join(__dirname, 'drivers', i))
	if stat.S_ISDIR(st.st_mode):
		#try:
			available_drivers[i] = import_module('drivers.%s' % i)
		#except ImportError, e:
		#	sys.stdout.write("Could not import ORM driver '%s': %s\n" % (i, e))


sys.path.remove(__dirname)
