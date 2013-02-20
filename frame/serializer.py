from orm.datatypes import CustomType
import json


class Serializer(object):
	def __init__(self, model):
		self.model = model

	def _resolve_prefix(self, prefix, key):
		if prefix:
			return '%s.%s' % ('.'.join(prefix), key)
		else:
			return key

	def _prepare_data(self, data, prefix=[]):
		temp = {}

		for k, v in data.items():
			key = self._resolve_prefix(prefix, k)
			if isinstance(v, CustomType):
				data_type = v.__class__.__name__
				temp[key] = {
					'dataType': data_type,
					'required': key in self.model.required_fields,
					'options': v.get_options()
				}

			elif isinstance(v, dict):
				new_prefix = list(prefix)
				new_prefix.append(k)
				temp[key] = self._prepare_data(v, new_prefix)

		return temp

	def serialize(self):
		return json.dumps(self._prepare_data(self.model.structure))
