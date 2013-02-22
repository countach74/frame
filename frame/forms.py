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
		
	def open_item_group(self, prefix):
		return self._environment.get_template('forms/open_item_group.html').render(title=prefix.title())
	
	def close_item_group(self):
		return self._environment.get_template('forms/close_item_group.html').render()

	def render(self, action, fields=None, failed_items=[], buttons=[SubmitType()],
		method='post', disable_validation=False, **kwargs):
			
		"""
		Generates HTML forms and, eventually, JavaScript validation to go along with
		those forms. Hopefully this will be a real time saver for CRUD.
		"""
			
		elements = []
		
		# Create new dictionary so we don't modify the default kwargs
		data = dict(kwargs)
		if 'id' not in data:
			data['id'] = uuid4()
			
		# If fields list is provided, sort the entries by it and do other cool stuff
		# like item grouping.
		if fields:
			last_prefix = None
			
			for i in fields:
				if '.' in i:
					split = i.split('.')
					prefix = split[-2]
					name = split[-1]
					
					if prefix != last_prefix:
						if last_prefix:
							elements.append(self.close_item_group())
							
						elements.append(self.open_item_group(prefix))
						last_prefix = prefix
						
				else:
					last_prefix = None
					name = i
						
				failed = i in failed_items
				item = self.structure_tree[i]
				
				if isinstance(item, CustomType):
					if self.data_tree and i in self.data_tree:
						value = self.data_tree[key]
					else:
						value = None
						
					elements.append(item.make_form_element(name, value, failed=failed))
					
				else:
					elements.append(make_form_element(name, None, failed=failed))
					
			if last_prefix:
				elements.append(self.close_item_group())

		else:
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
			form_elements=''.join(elements),
			method=method,
			validation_structure=validation_structure,
			**data)