from dotdict import DotDict
from jinja2 import PackageLoader
import sys
import os
from pkg_resources import iter_entry_points
import json


# Frame's library path
__frame_path = os.path.dirname(os.path.abspath(__file__))
__app_name = sys.argv[0]


config = DotDict({
	'application': {
		'name': 'Frame (%s)' % __app_name,
		'strip_trailing_slash': True,
		'dispatcher': 'routes',
		'debug': False,
	},
	
	'templates': {
		'directory': 'templates',
		'loaders': [PackageLoader('frame', 'templates')],
		'globals': {},
		'filters': {},
    'environment': {},
    'extension': '.html'
	},
	
	'preprocessors': [
		'handle_query_string',
		'form_url_decoder',
		'form_json_decoder',
		'form_multipart_decoder',
	],
	
	'postprocessors': [
		'handle_head_request',
		'add_last_modified',
		'add_date'
	],
	
	'hooks': [],

  'init_hooks': [],
	
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
	},
	
	'frame': {
		'path': __frame_path,
		'version': '0.2a',
	},
	
	'http_server': {
		'num_workers': 10,
	},
	
	'response': {
		'default_headers': {
			'Content-Type': 'text/html',
			'Server': 'Frame/0.2a',
		}
	},

  'jsonify': {
    'encoder': json.JSONEncoder
  }
})


if __name__ == '__main__':
	for entry_point in iter_entry_points('frame.config'):
		register_config = entry_point.load()
		register_config(config)

	config.prettify()

