from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer


TAG_URL = reverse('recipe:tag-list')


class PublicTagApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        response = self.client.post(TAG_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@gmail.com',
            'test123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Dessert")

        response = self.client.get(TAG_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            'test1@gamil.com',
            'test123456'
        )

        Tag.objects.create(user=user2, name='Fruity')
        tag = Tag.objects.create(user=self.user, name='Comfort Food')

        response = self.client.get(TAG_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], tag.name)
