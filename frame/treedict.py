class TreeDict(dict):
	"""
	An adapter to facilitate matching up validation for models and what not.
	"""
	
	def __init__(self, data=None):
		#self.data = self._prepare(data)
		self.original_data = data if data is not None else {}
		self._refresh()
		
	def _resolve_prefix(self, prefix, key):
		if prefix:
			return '%s.%s' % ('.'.join(prefix), key)
		else:
			return key
		
	def _prepare(self, source, destination={}, prefix=[]):
		for k, v in source.items():
			key = self._resolve_prefix(prefix, k)
			if isinstance(v, dict):
				new_prefix = list(prefix)
				new_prefix.append(k)
				self._prepare(source[k], destination, new_prefix)
			else:
				destination[key] = v
		return destination
		
	def _refresh(self):
		self.data = self._prepare(self.original_data, {})
		
	def _walk_items(self, key):
		indexes = key.split('.')
		last_item = self.original_data
		
		for i in indexes:
			last_item = last_item[i]
			
		return last_item
		
	def __setitem__(self, key, value):
		path = key.split('.')
		last_item = self.original_data
		
		for i in path[:-1]:
			if i not in last_item:
				last_item[i] = {}
			last_item = last_item[i]
		last_item[path[-1]] = value
		
		self._refresh()
	
	def __getitem__(self, key):
		self._refresh()
		return self._walk_items(key)
		
	def __delitem__(self, key):
		del(self.original_data[key])
		self._refresh()
		
	def __repr__(self):
		return str(self.data)
		
	__str__ = __repr__
	
	def __iter__(self):
		for i in self.data:
			yield i
			
	def __contains__(self, key):
		return key in self.data
		
	has_key = __contains__
		
	def __len__(self):
		return len(self.data)
		
	def __cmp__(self, other):
		if len(self) < len(other):
			return -1
		elif len(self) > len(other):
			return 1
		else:
			return 0
			
	def get_dict(self):
		return self.original_data
		
	def clear(self):
		self.original_data.clear()
		self._refresh()
		
	def copy(self):
		return TreeDict(self.original_data.copy())
		
	def fromkeys(self, seq, value=None):
		return self.data.fromkeys(seq, value)
		
	def get(self, key, default=None):
		return self.data.get(key, default)
		
	def items(self):
		return self.data.items()
		
	def iteritems(self):
		return self.data.iteritems()
		
	def iterkeys(self):
		return self.data.iterkeys()
		
	def itervalues(self):
		return self.data.itervalues()
		
	def keys(self):
		return self.data.keys()
		
	def pop(self, key, default=None):
		return self.data.pop(key, default)
		
	def popitem():
		return self.data.popitem()
		
	def setdefault(self, key, default=None):
		return self.data.setdefault(key, default)
		
	def update(self, *args, **kwargs):
		self.original_data.update(*args, **kwargs)
		self._refresh()
		
	def update_tree(self, data):
		for k, v in data.items():
			self[k] = v
		
	def values(self):
		return self.data.values()
		
	def viewitems(self):
		return self.data.viewitems()
		
	def viewkeys(self):
		return self.data.viewkeys()
		
	def viewvalues(self):
		return self.data.viewvalues()