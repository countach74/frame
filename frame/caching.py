"""
Provides simple caching interfaces. There are not any elaborate, intelligent caching
systems here... yet.
"""


__all__ = ['CacheOutput']


class Backend(object):
	def __init__(self, parent):
		self.parent = parent


class MemoryBackend(Backend):
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


class MemcacheBackend(Backend):
	import datetime

	def __init__(self, parent, cache, expires=900):
		self.parent = parent
		self.cache = cache
		self.expires = expires

	def __getitem__(self, key):
		return self.cache.get(key)

	def __setitem__(self, key, value):
		return self.cache.set(key, value, time=self.expires)

	def __contains__(self, key):
		return self.cache.get(key) is not None


class CacheOutput(object):
	import types
	_backend = None

	@classmethod
	def set_backend(self, backend, **options):
		self._backend = globals()['%sBackend' % backend](self, **options)

	@classmethod
	def get_backend(self):
		return self._backend

	def __init__(self, f):
		if self._backend is None:
			self._backend = MemoryBackend(self)

		self.f = f

	def __call__(self, *args, **kwargs):
		hashed_call = self.__hash(args, kwargs)

		if hashed_call not in self.get_backend():
			self.get_backend()[hashed_call] = self.f(*args, **kwargs)

		return self.get_backend()[hashed_call]

	def __get__(self, instance, owner=None):
		self.controller = instance
		return self.types.MethodType(self, instance)

	def __hash(self, args, kwargs):
		headers = self.controller.request.headers
		server_name = headers.server_name
		script_name = headers.script_name
		request_uri = headers.request_uri

		if script_name:
			whole_path = "%s%s/%s" % (server_name, script_name, request_uri)
		else:
			whole_path = "%s/%s" % (server_name, request_uri)

		return whole_path
		'''
		return "%s::%s::%s" % (
			hash(self.f),
			hash(frozenset(args)),
			hash(frozenset(kwargs.items())))
		'''
