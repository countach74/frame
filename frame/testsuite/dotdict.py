import unittest
from frame.dotdict import DotDict


class TestDotDict(unittest.TestCase):
	def setUp(self):
		self.data = DotDict({
			'name': {'first': 'Bob', 'last': 'Builder'},
			'email': 'bob@builder.com'
		})
		
	def test_assignment(self):
		self.data.name.first = 'Bobbert'
		assert self.data.name.first == self.data['name']['first']