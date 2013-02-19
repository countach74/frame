from orm.datatypes import CustomType, SubmitType


class BasicForm(object):
	_environment = None 

	def __init__(self, structure, data=None):
		self.structure = structure
		self.data = data

	def render(self, action, fields=None, failed_items=[], buttons=[SubmitType()], method='post', **kwargs):
		elements = []

		for key, value in self.structure.items():
			if (fields and key in fields) or not fields:
				failed = key in failed_items

				if isinstance(value, CustomType):
					if self.data and key in self.data:
						data_item = self.data[key]
					else:
						data_item = None

					elements.append(value.make_form_element(key, data_item, failed=failed))
	
				else:
					elements.append(CustomType.make_form_element(key, data_item, failed=failed))

		for i in buttons:
			elements.append(i.make_form_element())

		return self._environment.get_template('forms/wrapper.html').render(action=action,
			form_elements='\n'.join(elements), method=method, **kwargs)
