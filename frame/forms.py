from treedict import TreeDict
from orm.datatypes import CustomType, SubmitType, make_form_element
from uuid import uuid4


class BasicForm(object):
	_environment = None 

	def __init__(self, model, data=None):
		self.model = model
		self.structure = model.structure
		self.structure_tree = TreeDict(model.structure)
		self.data = data
		self.data_tree = TreeDict(data) if data else None

	def render(self, action, fields=None, failed_items=[], buttons=[SubmitType()],
		method='post', disable_validation=False, **kwargs):
			
		elements = []
		
		# Create new dictionary so we don't modify the default kwargs
		data = dict(kwargs)
		if 'id' not in data:
			data['id'] = uuid4()

		for key, value in self.structure_tree.iteritems():
			if (fields and key in fields) or not fields:
				failed = key in failed_items
				
				if isinstance(value, CustomType):
					if self.data_tree and key in self.data_tree:
						data_item = self.data_tree[key]
					else:
						data_item = None
					
					elements.append(value.make_form_element(key, data_item, failed=failed))
					
				else:
					elements.append(make_form_element(key, None, failed=failed))

		for i in buttons:
			elements.append(i.make_form_element())
		
		validation_structure = self.model.serialize() if not disable_validation else None

		return self._environment.get_template('forms/wrapper.html').render(
			action=action,
			form_elements='\n'.join(elements),
			method=method,
			validation_structure=validation_structure,
			**data)