class DotDict(dict):
	def __init__(self, *args, **kwargs):
		dict.__init__(self, *args, **kwargs)

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError, e:
			raise AttributeError(e)

	def __setattr__(self, key, value):
		self[key] = value
