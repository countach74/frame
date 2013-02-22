from treedict import TreeDict

# Setup default config
config = TreeDict({
	'sessions': {
		'backend': 'Memory',
		'cookie_name': 'FrameSession',
		'expires': 168,
		'enabled': True,
		
		'memcache': {
			'prefix': 'FRAME_SESSION::'
		},
		
		'memory': {
			'cleanup_frequency': 30,
		}
	},
	
	'orm': {
		'driver': 'mongo'
	},
	
	'pre_processors': ['form_url_encoder', 'form_ajax'],
	'post_processors': []
})