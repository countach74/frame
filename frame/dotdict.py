class DotDict(dict):
	def __init__(self, data):
		new_data = dict(data)
		
		for k, v in new_data.iteritems():
			if isinstance(v, dict):
				new_data[k] = DotDict(v)
		
		dict.__init__(self, new_data)

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError, e:
			raise AttributeError(e)

	def __setattr__(self, key, value):
		if isinstance(value, dict):
			self[key] = DotDict(value)
		else:
			self[key] = value
