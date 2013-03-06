from treedict import TreeDict
import sys
import os


# Frame's library path
__frame_path = os.path.dirname(os.path.abspath(__file__))


# Setup default config
config = TreeDict({
	'sessions': {
		'driver': 'file',
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
		'driver': 'mongo'
	},
	
	'application': {
		'name': 'FrameApp'
	},
	
	'pre_processors': ['form_url_encoder', 'form_json_encoder', 'form_multipart_encoder'],
	'post_processors': [],
	'timezone': 'America/Los_Angeles',
	'logger': {
		'driver': 'stdout',
		'production': {
			'options': {
				'facility': 'user'
			}
		},
		'stdout': {
			'options': {
				'out': sys.stdout,
				'err': sys.stderr
			}
		},
		'null': {
			'options': {}
		}
	},
	'static_map': {
		'/static': 'static',
		'/static/frame': os.path.join(__frame_path, 'static')
	}
})
