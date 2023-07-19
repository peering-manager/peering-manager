from unittest.mock import patch

from django.urls import reverse
from rest_framework import status

from utils.testing import APITestCase, APIViewTestCases

from ..models import *


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("devices-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ConfigurationTest(APIViewTestCases.View):
    model = Configuration
    brief_fields = ["id", "url", "display", "name"]
    create_data = [
        {"name": "Test1", "template": "test1_template"},
        {"name": "Test2", "template": "test2_template"},
        {"name": "Test3", "template": "test3_template"},
    ]
    bulk_update_data = {"template": "{{ router.hostname }}"}

    @classmethod
    def setUpTestData(cls):
        Configuration.objects.bulk_create(
            [
                Configuration(name="Example 1", template="example_1"),
                Configuration(name="Example 2", template="example_2"),
                Configuration(name="Example 3", template="example_3"),
            ]
        )


class PlatformTest(APIViewTestCases.View):
    model = Platform
    brief_fields = ["id", "url", "display", "name", "slug"]
    create_data = [
        {"name": "Test OS", "slug": "test-os"},
        {"name": "Bugs OS", "slug": "bugsos", "description": "Nice try one..."},
    ]
    bulk_update_data = {"description": "Favourite vendor"}

    @classmethod
    def setUpTestData(cls):
        Platform.objects.create(name="No Bugs OS", slug="nobugsos")
