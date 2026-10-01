import os
import sqlite3
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import DatabaseConnection


class SQLiteUploadTests(TestCase):
	def setUp(self):
		self.media_dir = tempfile.TemporaryDirectory()
		self.media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
		self.media_settings.enable()
		self.client = APIClient()
		self.client.force_authenticate(user=User.objects.create_user('upload-test-user'))

	def tearDown(self):
		self.media_settings.disable()
		self.media_dir.cleanup()

	def make_sqlite_upload(self, filename='analytics.sqlite3'):
		with tempfile.TemporaryDirectory() as folder:
			database_path = os.path.join(folder, 'fixture.sqlite3')
			connection = sqlite3.connect(database_path)
			connection.execute('CREATE TABLE reports (id INTEGER PRIMARY KEY)')
			connection.commit()
			connection.close()
			with open(database_path, 'rb') as database_file:
				contents = database_file.read()
		return SimpleUploadedFile(filename, contents, content_type='application/octet-stream')

	def test_valid_sqlite_database_upload_creates_active_connection(self):
		response = self.client.post('/api/v1/connections/', {
			'name': 'Analytics database',
			'engine': 'sqlite',
			'db_name': 'analytics.sqlite3',
			'sqlite_file': self.make_sqlite_upload(),
		}, format='multipart')

		self.assertEqual(response.status_code, 201)
		connection = DatabaseConnection.objects.get(pk=response.data['id'])
		self.assertTrue(os.path.isfile(connection.sqlite_file_path))
		self.assertNotEqual(os.path.basename(connection.sqlite_file_path), 'analytics.sqlite3')

	def test_non_sqlite_upload_is_rejected(self):
		response = self.client.post('/api/v1/connections/', {
			'name': 'Invalid database',
			'engine': 'sqlite',
			'db_name': 'invalid.db',
			'sqlite_file': SimpleUploadedFile('invalid.db', b'not a sqlite database'),
		}, format='multipart')

		self.assertEqual(response.status_code, 400)
		self.assertEqual(DatabaseConnection.objects.count(), 0)
