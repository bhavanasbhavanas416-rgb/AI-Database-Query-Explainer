import os
import sqlite3
import tempfile
from types import SimpleNamespace

from django.test import SimpleTestCase

from query_executor.services.query_runner import execute_sql_safely


class ReadOnlyQueryExecutionTests(SimpleTestCase):
	def setUp(self):
		self.temp_dir = tempfile.TemporaryDirectory()
		self.database_path = os.path.join(self.temp_dir.name, 'read_only_test.sqlite3')
		connection = sqlite3.connect(self.database_path)
		connection.execute('CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)')
		connection.execute("INSERT INTO items (name) VALUES ('original')")
		connection.commit()
		connection.close()
		self.database = SimpleNamespace(
			is_default_sample=False,
			engine='sqlite',
			sqlite_file_path=self.database_path,
		)

	def tearDown(self):
		self.temp_dir.cleanup()

	def test_select_and_explain_are_allowed(self):
		result = execute_sql_safely('SELECT name FROM items', self.database)
		explain = execute_sql_safely('EXPLAIN QUERY PLAN SELECT name FROM items', self.database)

		self.assertEqual(result['rows'], [['original']])
		self.assertTrue(explain['rows'])

	def test_write_and_stacked_statements_are_rejected(self):
		unsafe_queries = (
			"UPDATE items SET name='changed'",
			"INSERT INTO items (name) VALUES ('new')",
			'DELETE FROM items',
			'SELECT 1; SELECT 2',
		)
		for query in unsafe_queries:
			with self.subTest(query=query):
				with self.assertRaises(PermissionError):
					execute_sql_safely(query, self.database)

		connection = sqlite3.connect(self.database_path)
		value = connection.execute('SELECT name FROM items').fetchone()[0]
		connection.close()
		self.assertEqual(value, 'original')
