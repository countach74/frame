from treedict import TreeDict
import sys

# Setup default config
config = TreeDict({
	'sessions': {
		'driver': 'memory',
		'cookie_name': 'FrameSession',
		'expires': 168,
		'enabled': True,
		
		'memcache': {
			'prefix': 'FRAME_SESSION::',
			'connection': None,
		},
		
		'memory': {
			'cleanup_frequency': 30,
		}
	},
	
	'orm': {
		'driver': 'mongo'
	},
	
	'application': {
		'name': 'FrameApp'
	},
	
	'pre_processors': ['form_url_encoder', 'form_ajax'],
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
	}
})