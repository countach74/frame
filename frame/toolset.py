from urllib import quote_plus
from util import parse_query_string


class ToolSet(object):
	def __init__(self):
		self.app = None
		self.tools = {}

	def __getitem__(self, key):
		return self.tools[key]

	def __getattr__(self, key):
		try:
			return self.tools[key]
		except KeyError, e:
			raise AttributeError(e)

	def register(self, tool):
		if hasattr(tool, 'name'):
			tool_name = tool.name
		else:
			tool_name = tool.__name__.lower()
		self.tools[tool_name] = tool(self)


toolset = ToolSet()


class _ToolMeta(type):
	def __init__(cls, name, something, args):
		if name != 'Tool':
			toolset.register(cls)
		type.__init__(cls, name, something, args)


class Tool(object):
	__metaclass__ = _ToolMeta
	def __init__(self, toolset):
		self.toolset = toolset

	@property
	def app(self):
		return self.toolset.app


class Link(Tool):
	def __call__(self, url, label=None, **kwargs):
		script_name = self.app.request.headers.script_name

		url = script_name + url

		if not label:
			output = url

		else:
			if kwargs:
				tags = [' ']
				for k, v in kwargs.items():
					tags.append('%s="%s"' % (k, v))
			else:
				tags = ''

			output = '<a href="%s"%s>%s</a>' % (url, ' '.join(tags), label)

		return output


class Href(Link):
	pass

	
class CurrentUri(Tool):
	name = 'current_uri'
	
	def __call__(self, **kwargs):
		if 'query_string' in self.app.request.headers:
			query_string = self.app.request.headers.query_string
		else:
			query_string = ''
			
		data = parse_query_string(query_string)
		data.update(kwargs)
		
		path_info = self.app.request.headers.path_info
		items = map(self.make_query_item, data.iteritems())
		
		if items:
			return path_info + '?%s' % '&'.join(items)
		else:
			return path_info
		
	def make_query_item(self, item):
		key, value = map(str, item)
		return '%s=%s' % (key, quote_plus(value))


class GetPartialView(Tool):
	name = 'get_partial_view'

	def __call__(self, partial_view):
		return self.app.partial_views[partial_view]
