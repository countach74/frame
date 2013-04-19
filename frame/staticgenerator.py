import os


class StaticResponse(object):
	def __init__(self, generator, uri, response_body):
		self.generator = generator
		self.uri = uri
		self.response_body = response_body

	def save(self, path=None, filename='index.html', overwrite=False):
		if not path:
			path = os.path.join(
				self.generator.path,
				self.uri.lstrip('/'),
				filename
			)

		if not os.path.exists(os.path.dirname(path)):
			os.makedirs(os.path.dirname(path))

		if os.path.exists(path) and not overwrite:
			raise EnvironmentError("%s already exists." % path)

		with open(path, 'w') as f:
			f.write(self.response_body)


class StaticGenerator(object):
	def __init__(self, app, path):
		self.app = app
		self.path = path

	def generate(self, uris, environ=None, link_static_maps=True):
		if not environ:
			environ = {
				'REQUEST_METHOD': 'GET',
				'SCRIPT_NAME': '',
				'DOCUMENT_ROOT': os.getcwd(),
			}

		def start_response(status_line, headers):
			pass

		for uri in uris:
			e = dict(environ)
			e.update({
				'REQUEST_URI': uri,
				'PATH_INFO': uri
			})
			response_body = ''.join(self.app(e, start_response))
			yield StaticResponse(self, uri, response_body)

		if link_static_maps:
			self.link_static_maps()

	def link_static_maps(self):
		for k, v in self.app.static_map.items():
			path = os.path.join(self.path, k.lstrip('/'))
			os.symlink(v, path)


def generate_static_files(app, path, uris, overwrite=False):
	static_generator = StaticGenerator(app, path)
	map(lambda x: x.save(overwrite=overwrite), static_generator.generate(uris))
