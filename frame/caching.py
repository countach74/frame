"""
Provides simple caching interfaces. There are not any elaborate, intelligent caching
systems here... yet.
"""


class MemoryCacheBackend(object):
	from hashlib import sha1
	cache = {}

	def __getitem__(self, key):
		print "Get cache %s" % key
		return self.cache[key]

	def __setitem__(self, key, value):
		print "Save cache %s" % key
		self.cache[key] = value

	def __contains__(self, key):
		return key in self.cache


class CacheOutput(object):
	import types
	_backend = MemoryCacheBackend()

	@property
	def backend(self):
		return self._backend

	@backend.setter
	def backend(self, backend):
		self._backend = globals()['%sCacheBackend' % backend]()

	def __init__(self, f):
		self.f = f

	def __call__(self, *args, **kwargs):
		hashed_call = self.__hash(args, kwargs)

		if hashed_call not in self.backend:
			self.backend[hashed_call] = self.f(*args, **kwargs)

		return self.backend[hashed_call]

	def __get__(self, instance, owner=None):
		return self.types.MethodType(self, instance)

	def __hash(self, args, kwargs):
		return "%s::%s::%s" % (
			hash(self.f),
			hash(frozenset(args)),
			hash(frozenset(kwargs.items())))
