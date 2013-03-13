#!/usr/bin/env python

import os
import sys
from _config import config


def daemonize(app, host='127.0.0.1', port=8080, ports=None, server_type='fcgi', *args, **kwargs):
	def start_daemon(p):
		os.chdir("/")
		sid = os.setsid()
		os.umask(0)
		
		sys.stdin.close()
		sys.stdout.close()
		sys.stderr.close()
		
		if server_type == 'fcgi':
			app.start_fcgi(bindAddress=(host, p), *args, **kwargs)
		elif server_type == 'http':
			app.start_http(host=host, port=p, auto_reload=False, *args, **kwargs)
			
	
	if ports:
		for p in ports:
			pid = os.fork()
			if pid == 0:
				start_daemon(p)
	else:
		pid = os.fork()
		if pid == 0:
			start_daemon(port)