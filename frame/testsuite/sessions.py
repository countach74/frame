import unittest
import tempfile
import shutil
from frame._app import app
from frame._config import config
from frame.dotdict import DotDict
from frame.errors import SessionLoadError, SessionSaveError
from frame.extensions.sessions import SessionInterface, Session
from frame.response import Response

app.load_drivers()


class TestSession(unittest.TestCase):
	def setUp(self):
		app.request = DotDict({
			'headers': {},
			'cookies': {}
		})

		app.response = Response.from_data(
			'200 OK',
			{'Content-Type': 'text/html'},
			'This is a test response'
		)

		self.session_interface = app.drivers.session
		
	def test_session_load_error(self):
		app.request.cookies['FrameSession'] = Session.make_session_key()
		with self.assertRaises(SessionLoadError):
			session = self.session_interface.load_current()
			
	def test_session_force(self):
		session = self.session_interface.current(app, self.session_interface, True)
		
	def test_session_save(self):
		# Simulate first request
		session = self.session_interface.load_current()
		session['stuff'] = 'a test'
		app.request.cookies['FrameSession'] = session._key
		session.commit()
		
		# Simulate second request
		session = self.session_interface.load_current()
		
		# Assert that session data was indeed saved
		assert session['stuff'] == 'a test'
		
		
class TestMemorySession(TestSession):
	def setUp(self):
		config.sessions.driver = 'memory'
		
		TestSession.setUp(self)

	
class TestFileSession(TestSession):
	def setUp(self):
		self.temp_dir = tempfile.mkdtemp()
		
		config.sessions.driver = 'file'
		config.sessions.file.directory = self.temp_dir
		
		TestSession.setUp(self)
		
	def tearDown(self):
		shutil.rmtree(self.temp_dir)
		
		
class TestMemcacheSession(TestSession):
	def setUp(self):
		config.sessions.driver = 'memcache'
		
		try:
			import memcache
		except ImportError:
			self.skipTest("python-memcached not installed so not testing")
			
		TestSession.setUp(self)
