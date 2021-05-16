from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            'email': 'abc@gamil.com',
            'password': 'test123456',
            'name': 'abc'
        }

    def test_create_valid_user_success(self):
        response = self.client.post(CREATE_USER_URL, self.payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**response.data)
        self.assertTrue(user.check_password(self.payload['password']))
        self.assertNotIn('password', response.data)

    def test_user_exist(self):
        create_user(**self.payload)
        response = self.client.post(CREATE_USER_URL, self.payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        payload = self.payload.copy()
        payload['password'] = 'ab'
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user_exist = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exist)

    def test_create_token_for_user(self):
        payload = self.payload.copy()
        create_user(**payload)
        response = self.client.post(TOKEN_URL, {'email': 'abc@gamil.com',
            'password': 'test123456',})
        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        create_user(email='abc@gamil.com', password='123')
        response = self.client.post(TOKEN_URL, {'email': 'abc@gamil.com',
            'password': 'test123456'})
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        response = self.client.post(TOKEN_URL, {'email': 'abc@gamil.com',
            'password': 'test123456',})
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        response = self.client.post(TOKEN_URL, {'email':'check', 'password': ''})
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTest(TestCase):

    def setUp(self):
        self.user = create_user(**{
            'email': 'abc@gamil.com',
            'password': 'test123456',
            'name': 'abc'
        })
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'email': self.user.email,
            'name': self.user.name
        })

    def test_post_me_not_allowed(self):
        response = self.client.post(ME_URL, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        payload = {'name': 'test 1', 'password': 'password123'}
        response = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
