import pathlib
import os
import platform
import sqlite3


class Cacher(object):
	def __init__(self):
		make_new = False
		if not self.cache_db_path.exists():
			make_new = True

		self.connection = sqlite3.connect(str(self.cache_db_path))
		if make_new:
			self.create_tables()

	@property
	def cache_folder(self):
		home_folder = pathlib.Path.home()
		cache_folder = home_folder
		if platform.system() == "Windows":
			cache_folder = cache_folder / "AppData" / "Local" / ".openet_client"
		else:
			cache_folder = cache_folder /".openet_client"

		if not cache_folder.exists():
			os.makedirs(str(cache_folder))

		return cache_folder

	@property
	def cache_db_path(self):
		return self.cache_folder / "openet_client_cache.db"

	def create_tables(self):
		cursor = self.connection.cursor()
		cursor.execute("CREATE TABLE geodatabase (location text NOT NULL UNIQUE, openet_id text)")
		self.connection.commit()
		cursor.close()

	def cache_gdb_item(self, key, value):
		try:
			cursor = self.connection.cursor()
			cursor.execute("INSERT INTO geodatabase (location, openet_id) VALUES (?, ?)", (key, value))
			self.connection.commit()
			cursor.close()
		except sqlite3.IntegrityError:
			pass # theoretically we've already cached it then, but it's weird that it tried to retrieve it if we checked beforehand?

	def check_gdb_cache(self, key):
		cursor = self.connection.cursor()
		cursor.execute("SELECT openet_id from geodatabase where location=:location_key", {"location_key": key})
		for record in cursor.fetchall():
			value = record[0]  # since we're only selection openet_id and the location key is unique, it'll be the first item in the only tuple returned
			break
		else:
			value = False  # return False if we didn't find something - None will be used for items that exist but are Null
		cursor.close()
		return value