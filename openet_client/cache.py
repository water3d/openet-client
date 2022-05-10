import pathlib
import os
import platform
import sqlite3

import shelve
import tempfile
import datetime


class Cacher(object):
	def __init__(self):
		make_new = False
		if not self.cache_db_path.exists():
			make_new = True

		self.connection = sqlite3.connect(str(self.cache_db_path))

		if not make_new:  # if we don't already need to make the cache, then check to make sure it's up to date
			make_new = not self._check_cache_version()  # invert its logic since "check" would imply "make sure it's OK" so a result of True means it's fine

		if make_new:
			os.unlink(self.cache_db_path)  # make sure it doesn't exist before creating it -we might just have an out of date cache
			self.create_tables()

	def _check_cache_version(self):
		cursor = self.connection.cursor()
		cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
		tables = cursor.fetchall()

		if len(list({"geodatabase", "requests"} - set([table[0] for table in tables]))) > 0:  # if not all tables in the cache exist
			cursor.close()
			self.connection.close()
			return False

		return True

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
		cursor.execute("CREATE TABLE requests (url text NOT NULL, body text, response_code text, response_body text, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
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

	def cache_request(self, url, body, response_code, response_json):
		cursor = self.connection.cursor()
		cursor.execute("INSERT INTO requests (url, body, response_code, response_body) VALUES (?, ?, ?, ?)", (url, body, str(response_code), response_json))
		self.connection.commit()
		cursor.close()

	def save_shelf(self, data_structure):
		"""
			A way to cache larger data structures (just indexed by time in the shelf) before
			doing challenging work on them that might break
		:param data_structure:
		:return:
		"""
		shelf_file = tempfile.mktemp(prefix="et_data_", suffix=".shelf")
		shelf = shelve.open(shelf_file)
		shelf["data"] = data_structure
		shelf.sync()
		shelf.close()

