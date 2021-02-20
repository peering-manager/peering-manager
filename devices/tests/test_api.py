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
    brief_fields = ["id", "url", "name", "slug"]
    create_data = [
        {"name": "Cisco IOS", "slug": "cisco-ios"},
        {"name": "Arista EOS", "slug": "arista-eos", "napalm_driver": "eos"},
        {
            "name": "Cisco IOS-XR",
            "slug": "cisco-ios-xr",
            "napalm_driver": "iosxr",
            "description": "Nice try Cisco...",
        },
    ]

    @classmethod
    def setUpTestData(cls):
        Platform.objects.create(
            name="Juniper Junos", slug="juniper-junos", napalm_driver="junos"
        )
