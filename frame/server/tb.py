import sys, traceback

def do_crap():
	print crap

try:
	do_crap()
except Exception, e:
	e_type, e_value, e_traceback = sys.exc_info()

	#traceback.print_tb(e_traceback, 1)
	print traceback.format_exception(e_type, e_value, e_traceback)
