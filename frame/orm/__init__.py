import os
import sys
import stat
from importlib import import_module
from datatypes import *

# Import global config
from frame._config import config


available_drivers = {}

__dirname = os.path.dirname(os.path.abspath(__file__))

sys.path.append(__dirname)

# Populate available_drivers
for i in os.listdir(os.path.join(__dirname, 'drivers')):
	st = os.stat(os.path.join(__dirname, 'drivers', i))
	if stat.S_ISDIR(st.st_mode):
		try:
			available_drivers[i] = import_module('drivers.%s' % i)
		except ImportError, e:
			pass


sys.path.remove(__dirname)
