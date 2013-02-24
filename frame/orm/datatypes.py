"""
Defines a handful of custom types to use when defining your model's data structure.
"""

from errors import *
import types
import re


class CustomType(object):
	template = 'forms/elements/generic_element.html'

	def __init__(self, data={}, **kwargs):
		self.kwargs = kwargs
		self.kwargs.update(data)

	def check_type(self, instance, parent):
		return isinstance(instance, parent)

	def make_form_element(self, title, key, value=None, new=False, failed=False):
		return (self._environment
			.get_template(self.template)
			.render(key=key, title=title, value=value, arguments=self.kwargs, new=new, failed=failed))

	def get_options(self):
		options = {}
		options.update(self.kwargs)

		for i in dir(self):
			attr = getattr(self, i)
			if not any((hasattr(attr, '__call__'), i.startswith('_'), i in ('kwargs', 'template'))):
				options[i] = attr

		return options


def make_form_element(title, key, value=None, new=False, failed=False):
	return (CustomType._environment
		.get_template('forms/elements/generic_element.html')
		.render(key=key, title=title, value=value, new=new, failed=failed))


class SubmitType(CustomType):
	def __init__(self, label="Submit", *args, **kwargs):
		self.label = label
		CustomType.__init__(self, *args, **kwargs)

	def make_form_element(self):
		return (self._environment.get_template('forms/elements/submit.html')
			.render(label=self.label, arguments=self.kwargs))


class StringType(CustomType):
	def __init__(self, charset=None, min_length=None, max_length=None, *args, **kwargs):
		self.charset = charset
		self.min_length = min_length
		self.max_length = max_length
		CustomType.__init__(self, *args, **kwargs)

	def __call__(self, string):
		string = str(string)

		if self.charset and not all((i in self.charset for i in string)):
			raise ValidateError("Invalid characters in string")

		elif self.min_length is not None and len(string) < self.min_length:
			raise ValidateError("String too short. Minimum length: %s" % self.min_length)

		elif self.max_length is not None and len(string) > self.max_length:
			raise ValidateError("String too long. Maximum length: %s" % self.max_length)

		return string

	def __repr__(self):
		return "<string>"


class PasswordType(StringType):
	template = 'forms/elements/password.html'


class BoolType(CustomType):
	def __init__(self, style='radio', choices={'true': 'True', 'false': 'False'}, default='true', *args, **kwargs):
		self.style = style
		self.choices = choices
		self.default = default
		CustomType.__init__(self, *args, **kwargs)

	def __call__(self, value):
		return str(value).lower() in ('true', '1', 't')

	def __repr__(self):
		return "<bool>"

	def make_form_element(self, title, key, new=False, value=None, failed=False):
		return (self._environment.get_template('forms/elements/%s.html' % self.style).render(
			key=key, value=value, title=key.title(), choices=self.choices,
			default=self.default, new=new, failed=failed))


class IntType(CustomType):
	def __init__(self, minimum=None, maximum=None, *args, **kwargs):
		self.minimum = minimum
		self.maximum = maximum
		CustomType.__init__(self, *args, **kwargs)

	def __call__(self, i):
		try:
			i = int(i)
		except ValueError:
			raise ValidateError("Invalid integer: %s" % i)

		if self.minimum is not None and i < self.minimum:
			raise ValidateError("Integer too small. Smallest allowed value: %s" % self.minimum)

		elif self.maximum is not None and i > self.maximum:
			raise ValidateError("Integer too large. Largest allowed value: %s" % self.maximum)

		return i

	def __repr__(self):
		return "<int>"


class FloatType(IntType):
	def __call__(self, f):
		try:
			f = float(f)
		except ValueError:
			raise ValidateError("Invalid float: %s" % f)

		if self.minimum is not None and i < self.minimum:
			raise ValidateError("Number too small. Smallest allowed value: %s" % self.minimum)

		elif self.maximum is not None and i > self.maximum:
			raise ValidateError("Number too large. Largest allowed value: %s" % self.maximum)

		return f

	def __repr__(self):
		return "<float>"


class EmailType(CustomType):
	_pattern = re.compile("^[a-zA-Z0-9\._%+\-]+@[a-zA-Z0-9_\-]+[a-zA-Z0-9_\-\.]*\.[a-zA-Z]{2,3}")

	def __init__(self, max_length=None, *args, **kwargs):
		self.max_length = max_length
		CustomType.__init__(self, *args, **kwargs)

	def __call__(self, email):
		match = re.match(self._pattern, email)

		if (self.max_length and len(email) > self.max_length) or not match:
			self.raise_error(email)

		return email
	
	def raise_error(self, email):
		raise ValidateError("Could not validate e-mail address '%s'" % email)

	def __repr__(self):
		return "<email>"

	def make_form_element(self, title, key, value=None, new=False, failed=False):
		return (self._environment.get_template('forms/elements/email.html')
			.render(key=key, value=value, title=key.title(), new=new, failed=failed))


class ListType(CustomType):
	def __init__(self, children_type=None, max_length=None, style='select', choices={}, default=None, *args, **kwargs):
		self.children_type = children_type
		self.max_length = max_length
		self.style = style
		self.choices = choices
		self.default = default
		CustomType.__init__(self, *args, **kwargs)

	def __call__(self, lst):
		if self.children_type:
			for i in xrange(len(lst)):
				item = lst[i]
				if not self.check_type(item, self.children_type):
					try:
						lst[i] = self.children_type(item)
					except:
						raise ValidateError("Not all list items are of the type: item %s" % i)

		return lst

	def __repr__(self):
		return "<list>"

	def make_form_element(self, title, key, value=None, new=False, failed=False):
		return (self._environment.get_template('forms/elements/%s.html' % self.style).render(
			key=key, value=value, title=key.title(), choices=self.choices,
			default=self.default, new=new, failed=failed))
