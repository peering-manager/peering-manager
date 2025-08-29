from django.urls import reverse
from rest_framework import status

from peering.models import AutonomousSystem
from utils.testing import APITestCase, APIViewTestCases

from ..enums import *
from ..models import *


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("devices-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ConfigurationTest(APIViewTestCases.View):
    model = Configuration
    brief_fields = ["id", "url", "display_url", "display", "name"]
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
    query_fields = ["id", "url", "display"]
    brief_fields = ["id", "url", "display", "name", "slug"]
    create_data = [
        {"name": "Test OS", "slug": "test-os"},
        {"name": "Bugs OS", "slug": "bugsos", "description": "Nice try one..."},
    ]
    bulk_update_data = {"description": "Favourite vendor"}

    @classmethod
    def setUpTestData(cls):
        Platform.objects.create(name="No Bugs OS", slug="nobugsos")


class RouterTest(APIViewTestCases.View):
    model = Router
    brief_fields = ["id", "url", "display_url", "display", "name", "hostname"]
    bulk_update_data = {"status": DeviceStatus.MAINTENANCE}

    @classmethod
    def setUpTestData(cls):
        cls.local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        cls.platform = Platform.objects.create(name="No Bugs OS", slug="nobugsos")
        cls.template = Configuration.objects.create(
            name="Test", template="Nothing useful"
        )
        Router.objects.bulk_create(
            [
                Router(
                    name="Example 1",
                    hostname="1.example.com",
                    status=DeviceStatus.ENABLED,
                    configuration_template=cls.template,
                    local_autonomous_system=cls.local_autonomous_system,
                ),
                Router(
                    name="Example 2",
                    hostname="2.example.com",
                    status=DeviceStatus.ENABLED,
                    configuration_template=cls.template,
                    local_autonomous_system=cls.local_autonomous_system,
                ),
                Router(
                    name="Example 3",
                    hostname="3.example.com",
                    status=DeviceStatus.ENABLED,
                    configuration_template=cls.template,
                    local_autonomous_system=cls.local_autonomous_system,
                ),
            ]
        )
        cls.router = Router.objects.get(hostname="1.example.com")
        cls.create_data = [
            {
                "name": "Test 1",
                "hostname": "test1.example.com",
                "status": DeviceStatus.ENABLED,
                "configuration_template": cls.template.pk,
                "local_autonomous_system": cls.local_autonomous_system.pk,
                "platform": cls.platform.pk,
            },
            {
                "name": "Test 2",
                "hostname": "test2.example.com",
                "status": DeviceStatus.MAINTENANCE,
                "configuration_template": cls.template.pk,
                "local_autonomous_system": cls.local_autonomous_system.pk,
                "platform": cls.platform.pk,
            },
            {
                "name": "Test 3",
                "hostname": "test3.example.com",
                "status": DeviceStatus.DISABLED,
                "configuration_template": cls.template.pk,
                "local_autonomous_system": cls.local_autonomous_system.pk,
                "platform": cls.platform.pk,
            },
        ]

    def test_configuration(self):
        url = reverse("devices-api:router-configuration", kwargs={"pk": self.router.pk})
        response = self.client.get(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)

    def test_poll_bgp_sessions(self):
        url = reverse(
            "devices-api:router-poll-bgp-sessions", kwargs={"pk": self.router.pk}
        )
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)

    def test_test_napalm_connection(self):
        url = reverse(
            "devices-api:router-test-napalm-connection", kwargs={"pk": self.router.pk}
        )
        response = self.client.get(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)

    def test_update_from_netbox(self):
        url = reverse("devices-api:router-update-from-netbox")
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(
            url, **self.header, data={"event": "created"}, format="json"
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(
            url, **self.header, data={"data": {}}, format="json"
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

        data = {
            "event": "created",
            "data": {
                "id": 1,
                "url": "/api/dcim/devices/1/",
                "display": "router.example.net",
                "name": "router.example.net",
                "device_role": {
                    "id": 7,
                    "url": "/api/dcim/device-roles/7/",
                    "display": "Router",
                    "name": "Router",
                    "slug": "router",
                },
                "platform": {
                    "id": 9,
                    "url": "/api/dcim/platforms/9/",
                    "display": "Malfunctioning OS",
                    "name": "Malfunctioning OS",
                    "slug": "malfunctioning-os",
                },
                "status": {"value": "active", "label": "Active"},
                "local_context_data": None,
                "tags": [],
            },
        }
        response = self.client.post(url, **self.header, data=data, format="json")
        self.assertHttpStatus(response, status.HTTP_501_NOT_IMPLEMENTED)

        data = {
            "event": "created",
            "data": {
                "id": 1,
                "url": "/api/dcim/devices/1/",
                "display": "router.example.net",
                "name": "router.example.net",
                "device_role": {
                    "id": 7,
                    "url": "/api/dcim/device-roles/7/",
                    "display": "Router",
                    "name": "Router",
                    "slug": "router",
                },
                "platform": {
                    "id": 3,
                    "url": "/api/dcim/platforms/3/",
                    "display": "Juniper Junos",
                    "name": "Juniper Junos",
                    "slug": "juniper-junos",
                },
                "status": {"value": "active", "label": "Active"},
                "local_context_data": None,
                "tags": [],
            },
        }
        response = self.client.post(url, **self.header, data=data, format="json")
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(Router.objects.get(netbox_device_id=1).status, "enabled")

        data = {
            "event": "updated",
            "data": {
                "id": 1,
                "url": "/api/dcim/devices/1/",
                "display": "router.example.net",
                "name": "router.example.net",
                "device_role": {
                    "id": 7,
                    "url": "/api/dcim/device-roles/7/",
                    "display": "Router",
                    "name": "Router",
                    "slug": "router",
                },
                "platform": {
                    "id": 3,
                    "url": "/api/dcim/platforms/3/",
                    "display": "Juniper Junos",
                    "name": "Juniper Junos",
                    "slug": "juniper-junos",
                },
                "status": {"value": "offline", "label": "Offline"},
                "local_context_data": None,
                "tags": [],
            },
        }
        response = self.client.post(url, **self.header, data=data, format="json")
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(Router.objects.get(netbox_device_id=1).status, "disabled")

        data = {
            "event": "deleted",
            "data": {
                "id": 1,
                "url": "/api/dcim/devices/1/",
                "display": "router.example.net",
                "name": "router.example.net",
                "device_role": {
                    "id": 7,
                    "url": "/api/dcim/device-roles/7/",
                    "display": "Router",
                    "name": "Router",
                    "slug": "router",
                },
                "platform": {
                    "id": 3,
                    "url": "/api/dcim/platforms/3/",
                    "display": "Juniper Junos",
                    "name": "Juniper Junos",
                    "slug": "juniper-junos",
                },
                "status": {"value": "offline", "label": "Offline"},
                "local_context_data": None,
                "tags": [],
            },
        }
        response = self.client.post(url, **self.header, data=data, format="json")
        self.assertHttpStatus(response, status.HTTP_200_OK)
        with self.assertRaises(Router.DoesNotExist):
            Router.objects.get(netbox_device_id=1)
