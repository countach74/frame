from dotdict import DotDict
import sys
import os


# Frame's library path
__frame_path = os.path.dirname(os.path.abspath(__file__))
__app_name = sys.argv[0]


config = DotDict({
	'sessions': {
		'driver': 'memory',
		'cookie_name': 'FrameSession',
		'expires': 168,
		'cleanup_frequency': 30,
		'enabled': True,
		
		'memcache': {
			'prefix': 'FRAME_SESSION::',
			'connection': None,
		},
		
		'memory': {
		},
		'file': {
			'directory': 'sessions',
		},
		'mysql': {
			'host': 'localhost',
			'port': 3306,
			'connection': None,
			'database': None,
			'user': None,
			'password': None,
			'table': 'frame_sessions'
		}
	},
	
	'orm': {
		'driver': None
	},
	
	'application': {
		'name': 'Frame (%s)' % __app_name,
		'strip_trailing_slash': True
	},
	
	'pre_processors': ['form_url_encoder', 'form_json_encoder', 'form_multipart_encoder'],
	'post_processors': [],
	'timezone': 'America/Los_Angeles',
	'logger': {
		'driver': 'stdout',
		'production': {
			'facility': 'user',
			'out': sys.stdout,
			'err': sys.stderr
		},
		'stdout': {
			'out': sys.stdout,
			'err': sys.stderr
		},
		'null': {}
	},
	'static_map': {
		'/static': 'static',
		'/static/frame': os.path.join(__frame_path, 'static')
	}
})