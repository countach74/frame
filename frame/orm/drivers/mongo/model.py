from bson import ObjectId
from frame.orm.errors import ValidateError, RequiredFieldError, ExtraFieldError, ModelLoadError
from frame.orm.datatypes import CustomType
from frame.forms import BasicForm
from frame.serializer import Serializer


class Model(object):
	structure = {}
	required_fields = []
	default_values = {}
	unique_fields = []
	hidden_fields = []

	def __init__(self, data={}, **kwargs):
		# Weird work around for some sort of pointer issue?
		data = dict(data)

		if '_id' not in data and '_id' not in kwargs:
			data['_id'] = ObjectId()

		# Setup data with defaults
		defaults = dict(self.default_values)
		self._setup_defaults(defaults)

		# Check if any of the defaults are callables; call and return values if they are
		self._data = defaults
		self._data.update(data)
		self._data.update(kwargs)

		# Change "make_form" method to point to "make_edit_form"
		self.make_form = self.make_edit_form

	def __getitem__(self, key):
		if key in self._data:
			return self._data[key]
		elif key in self.structure:
			return None
		else:
			raise KeyError("Could not access item %s" % key)

	def __setitem__(self, key, value):
		if key in self.structure:
			self._data[key] = value
		else:
			raise KeyError("Cannot save the key '%s' as it is not defind as part of this data structure." % key)

	def __delitem__(self, key):
		del(self._data[key])

	def __getattr__(self, key):
		if key in self._data:
			return self._data[key]
		elif key in self.structure:
			return None
		else:
			raise AttributeError(e)

	def __delattr__(self, key):
		try:
			del(self._data[key])
		except KeyError, e:
			raise AttributeError(e)

	def __setattr__(self, key, value):
		if key in ('_data', 'make_form'):
			object.__setattr__(self, key, value)
		elif key in self.structure:
			self._data[key] = value
		else:
			raise AttributeError("Cannot set attribute %s" % key)

	def __contains__(self, key):
		return key in self._data

	def __repr__(self):
		data = dict(self.structure)
		data.update(self._data)
		return str(data)

	@classmethod
	def make_new_form(self, data={}, failed_items=[], *args, **kwargs):
		return BasicForm(self.structure, data).render(failed_items=failed_items, *args, **kwargs)

	def make_edit_form(self, failed_items=[], *args, **kwargs):
		return BasicForm(self.structure, self._data).render(failed_items=failed_items, *args, **kwargs)

	make_form = make_new_form

	def items(self):
		return self._data.items()

	def update(self, data):
		self._data.update(data)

	def _setup_defaults(self, data):
		if isinstance(data, dict):
			for k, v in data.items():
				if isinstance(v, dict) or hasattr(v, '__iter__'):
					self._setup_defaults(v)
				elif hasattr(v, '__call__'):
					data[k] = v()
		elif hasattr(data, '__iter__'):
			for i in xrange(len(data)):
				if hasattr(data[i], '__call__'):
					data[i] = data[i]()

	@property
	def collection(self):
		return self.get_collection()

	@classmethod
	def get_collection(self):
		return self.__connection__[self.__database__][self.__collection__]

	def save(self, safe=True, *args, **kwargs):
		self.validate()

		# Workaround weird bug...
		if safe:
			return self.get_collection().save(self._data, safe=True, *args, **kwargs)
		else:
			return self.get_collection().save(self._data, *args, **kwargs)

	def remove(self):
		self.collection.remove({'_id': self._id})

	def _check_required_fields(self):
		missing_fields = []
		for i in self.required_fields:
			docs = i.split('.')
			last_item = self._data

			for j in docs:
				if j in last_item:
					last_item = last_item[j]
				else:
					missing_fields.append(i)
					break
		if missing_fields:
			raise RequiredFieldError("Required field(s) missing: %s" % ', '.join(missing_fields))

	def _check_for_extra_fields(self):
		structure = self.structure.keys()
		data = self._data.keys()
		extra_fields = []

		for i in data:
			if i not in structure and i != '_id':
				extra_fields.append(i)

		if extra_fields:
			raise ExtraFieldError("Found extra field(s) in data: %s" % ', '.join(extra_fields))

	def _get_structure_item(self, key_chain):
		last_item = self.structure

		for i in key_chain:
			if i in last_item:
				last_item = last_item[i]
			else:
				break

		return last_item

	def _check_data_types(self, data, structure, extra_fields=[]):
		for k, v in filter(lambda (x, y): x != '_id', data.items()):
			if isinstance(v, dict):
				self._check_data_types(data[k], structure[k], extra_fields)
			else:
				if k in structure and isinstance(structure[k], CustomType):
					data[k] = structure[k](v)
				elif k not in structure:
					extra_fields.append(k)
				elif not isinstance(v, structure[k]):
					try:
						data[k] = structure[k](v)
					except KeyError:
						extra_fields.append(k)
					except Exception, e:
						raise ValidateError("Could not properly convert %s" % k)

	def validate(self):
		extra_fields = []

		self._check_required_fields()
		self._check_data_types(self._data, self.structure, extra_fields)
		if extra_fields:
			raise ExtraFieldError("Found extra field(s) in data: %s" % ', '.join(extra_fields))
			
	@classmethod
	def find(self, *args, **kwargs):
		result = self.get_collection().find(*args, **kwargs)
		for i in result:
			yield self(i)

	@classmethod
	def find_one(self, *args, **kwargs):
		result = self.get_collection().find_one(*args, **kwargs)
		if result:
			return self(result)
		else:
			return None

	@classmethod
	def ensure_index(self, *args, **kwargs):
		return self.get_collection().ensure_index

	@classmethod
	def create_index(self, *args, **kwargs):
		return self.get_collection().create_index

	@classmethod
	def serialize(self):
		return Serializer(self).serialize()
