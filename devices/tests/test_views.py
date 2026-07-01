from django.contrib.auth.models import Permission
from django.urls import reverse

from peering.models import AutonomousSystem
from utils.testing import ViewTestCases

from ..enums import *
from ..models import *


class ConfigurationTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Configuration

    test_bulk_edit_objects = None

    @classmethod
    def setUpTestData(cls):
        Configuration.objects.bulk_create(
            [
                Configuration(name="Configuration 1", template="Configuration 1"),
                Configuration(name="Configuration 2", template="Configuration 2"),
                Configuration(name="Configuration 3", template="Configuration 3"),
            ]
        )

        cls.form_data = {
            "name": "Configuration 4",
            "template": "Configuration 4",
            "comments": "",
            "tags": [],
        }


class PlatformTestCase(
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
):
    model = Platform

    @classmethod
    def setUpTestData(cls):
        Platform.objects.bulk_create(
            [
                Platform(name="Some OS", slug="someos"),
                Platform(name="Test OS", slug="testos"),
            ]
        )

        cls.form_data = {
            "name": "Bugs OS",
            "slug": "bugsos",
            "napalm_driver": "bugsos",
            "napalm_args": {},
            "password_algorithm": "",
            "description": "",
        }


class RouterTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Router

    @classmethod
    def setUpTestData(cls):
        local_as = AutonomousSystem.objects.create(asn=64500, name="Autonomous System", affiliated=True)

        Router.objects.bulk_create(
            [
                Router(
                    name="Router 1",
                    hostname="router1.example.net",
                    local_autonomous_system=local_as,
                    status=DeviceStatus.ENABLED,
                ),
                Router(
                    name="Router 2",
                    hostname="router2.example.net",
                    local_autonomous_system=local_as,
                    status=DeviceStatus.ENABLED,
                ),
                Router(
                    name="Router 3",
                    hostname="router3.example.net",
                    local_autonomous_system=local_as,
                    status=DeviceStatus.ENABLED,
                ),
            ]
        )

        cls.form_data = {
            "name": "Router 4",
            "hostname": "router4.example.net",
            "configuration_template": None,
            "local_autonomous_system": local_as.pk,
            "encrypt_passwords": False,
            "platform": None,
            "status": DeviceStatus.ENABLED,
            "netbox_device_id": 0,
            "comments": "",
            "tags": [],
            "napalm_args": None,
            "napalm_password": None,
            "napalm_timeout": 30,
            "napalm_username": "",
        }
        cls.bulk_edit_data = {"comments": "New comments"}

    def test_bulk_configuration_requires_permission(self):
        url = reverse("devices:router_bulk_configuration")
        pks = list(Router.objects.values_list("pk", flat=True))
        self.assertHttpStatus(self.client.post(url, data={"pk": pks}), 403)

    def test_bulk_configuration_review(self):
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label="devices", codename="deploy_router_configuration")
        )
        url = reverse("devices:router_bulk_configuration")
        pks = list(Router.objects.values_list("pk", flat=True)[:2])

        response = self.client.post(url, data={"pk": pks})
        self.assertHttpStatus(response, 200)
        content = response.content.decode()
        self.assertIn("Router 1", content)
        self.assertIn("Router 2", content)

    def test_bulk_configuration_no_selection_redirects(self):
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label="devices", codename="deploy_router_configuration")
        )
        url = reverse("devices:router_bulk_configuration")
        response = self.client.post(url, data={"pk": []})
        self.assertRedirects(response, reverse("devices:router_list"), fetch_redirect_response=False)
