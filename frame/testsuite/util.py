import unittest
import datetime
from frame import util



class SimpleUtilTests(unittest.TestCase):
	def test_format_date(self):
		timestamp_string = "Wed, 13 Mar 2013 15:13:45 GMT"
		hard_coded_date = datetime.datetime.strptime(
			timestamp_string, "%a, %d %b %Y %H:%M:%S GMT")
			
		self.assertTrue(util.format_date(hard_coded_date) == timestamp_string)
		
	def test_singleton(self):
		class S(util.Singleton):
			pass
		
		s1 = S()
		s2 = S()
		
		self.assertEqual(s1, s2, "Singleton classes should all return "
			"same instance")
			
	def test_truncate(self):
		lorem_ipsum = (
			"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam nec purus quis"
			"ante convallis blandit sit amet et velit. Nam mollis, justo nec aliquam condimentum,"
			"orci magna pellentesque libero, sed iaculis leo massa id tortor. Nullam pretium"
			"tellus at lorem aliquet venenatis. Nulla placerat mattis congue. Sed sit amet dui"
			"vitae ante tristique ultricies. Aenean et massa in lacus iaculis rhoncus ac in augue."
			"Suspendisse potenti. Donec nec tellus et metus viverra consequat. Donec lectus sem,"
			"rhoncus vel sollicitudin eu, pharetra ultrices mi. Maecenas quis rhoncus felis. Nulla"
			"facilisi.")
			
		self.assertTrue(len(util.truncate(lorem_ipsum)) <= 33, "Truncated text should not be "
			"longer than 33 characters")
			
		self.assertTrue(util.truncate('') == '')
			
	def test_parse_query_string(self):
		hard_coded_data = {
			'name': 'poo',
			'file1': ['thing', 'thing2'],
			'another_thing': 'a test'
		}
		
		query_string = "name=poo&file1=thing&file1=thing2&another_thing=a%20test"
		data = util.parse_query_string(query_string)
		
		self.assertEqual(data, hard_coded_data)
		

if __name__ == '__main__':
	unittest.main()