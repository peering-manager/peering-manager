from unittest.mock import patch

from django.urls import reverse
from rest_framework import status

from devices.models import Platform
from utils.testing import APITestCase, StandardAPITestCases


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("devices-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PlatformTest(StandardAPITestCases.View):
    model = Platform
    brief_fields = ["id", "url", "display", "name", "slug"]
    create_data = [
        {"name": "Test OS", "slug": "test-os"},
        {"name": "Bugs OS", "slug": "bugsos", "description": "Nice try one..."},
    ]

    @classmethod
    def setUpTestData(cls):
        Platform.objects.create(name="No Bugs OS", slug="nobugsos")
