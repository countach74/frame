import pymongo
import pymongo.database as database
import pymongo.collection as collection
from model import Model


class Collection(collection.Collection):
	def __init__(self, *args, **kwargs):
		collection.Collection.__init__(self, *args, **kwargs)
		self.connection = self.database.connection

	def __getitem__(self, key):
		if key in self.connection.models:
			model = self.connection.models[key]
			model.__collection__ = self.name
			model.__database__ = self.database.name
			return model
		else:
			return collection.Collection.__getitem__(self, key)

	def __getattr__(self, key):
		if key in self.connection.models:
			model = self.connection.models[key]
			model.__collection__ = self.name
			model.__database__ = self.database.name
			return model
		else:
			return collection.Collection.__getattr__(self, key)


class Database(database.Database):
	def __init__(self, *args, **kwargs):
		database.Database.__init__(self, *args, **kwargs)

	def __getitem__(self, key):
		return Collection(self, key)

	__getattr__ = __getitem__


class Connection(pymongo.Connection):
	def __init__(self, *args, **kwargs):
		self.models = {}

		pymongo.Connection.__init__(self, *args, **kwargs)

	def __getitem__(self, key):
		return Database(self, key)

	__getattr__ = __getitem__

	def register(self, c):
		self.models[c.__name__] = c
		c.__connection__ = self
		return c
