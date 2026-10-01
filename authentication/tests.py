from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient


class RegistrationTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_registration_starts_session_without_granting_admin_role(self):
		response = self.client.post('/api/v1/auth/register/', {
			'username': 'admin',
			'email': 'admin@example.com',
			'password': 'test-password-123',
		}, format='json')

		self.assertEqual(response.status_code, 201)
		user = User.objects.get(username='admin')
		self.assertEqual(user.profile.role, 'user')
		self.assertEqual(self.client.get('/api/v1/auth/profile/').status_code, 200)
		self.assertFalse(self.client.get('/api/v1/auth/profile/').data['is_admin'])

	def test_dashboard_sets_csrf_cookie_for_session_requests(self):
		client = APIClient(enforce_csrf_checks=True)
		response = client.get('/')

		self.assertEqual(response.status_code, 200)
		self.assertIn('csrftoken', client.cookies)

	def test_database_and_query_apis_require_authentication(self):
		endpoints = (
			('get', '/api/v1/connections/'),
			('get', '/api/v1/schema/'),
			('post', '/api/v1/query/generate/'),
			('post', '/api/v1/query/execute/'),
			('get', '/api/v1/query/history/'),
			('post', '/api/v1/analytics/chart/'),
			('get', '/api/v1/admin/metrics/'),
		)
		for method, url in endpoints:
			with self.subTest(url=url):
				response = getattr(self.client, method)(url)
				self.assertIn(response.status_code, (401, 403))
