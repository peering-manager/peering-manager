from django.test import TestCase

from peering.models import AutonomousSystem
from utils.testing import BaseFilterSetTests

from ..enums import *
from ..filtersets import *
from ..models import *


class ConfigurationTestCase(TestCase, BaseFilterSetTests):
    queryset = Configuration.objects.all()
    filterset = ConfigurationFilterSet

    @classmethod
    def setUpTestData(cls):
        Configuration.objects.bulk_create(
            [
                Configuration(name="Configuration 1", template="Configuration 1"),
                Configuration(name="Configuration 2", template="Configuration 2"),
                Configuration(name="Configuration 3", template="Configuration 3"),
            ]
        )

    def test_name(self):
        params = {"q": "Configuration 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class PlatformTestCase(TestCase, BaseFilterSetTests):
    queryset = Platform.objects.all()
    filterset = PlatformFilterSet

    def test_q(self):
        params = {"q": "Juniper"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "cisco-ios"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {"name": ["Juniper Junos"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"name": ["Juniper Junos", "Cisco IOS"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {"slug": ["juniper-junos"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"slug": ["juniper-junos", "cisco-ios"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class RouterTestCase(TestCase, BaseFilterSetTests):
    queryset = Router.objects.all()
    filterset = RouterFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.local_as = AutonomousSystem.objects.create(
            asn=64501, name="Autonomous System 1", affiliated=True
        )
        cls.configuration = Configuration.objects.create(
            name="Configuration 1", template="Configuration 1"
        )
        Router.objects.bulk_create(
            [
                Router(
                    name="Router 1",
                    hostname="router1.example.net",
                    status=DeviceStatus.ENABLED,
                    encrypt_passwords=True,
                    local_autonomous_system=cls.local_as,
                ),
                Router(
                    name="Router 2",
                    hostname="router2.example.net",
                    status=DeviceStatus.DISABLED,
                    encrypt_passwords=True,
                    local_autonomous_system=cls.local_as,
                ),
                Router(
                    name="Router 3",
                    hostname="router3.example.net",
                    status=DeviceStatus.ENABLED,
                    configuration_template=cls.configuration,
                    local_autonomous_system=cls.local_as,
                ),
            ]
        )

    def test_q(self):
        params = {"q": "Router 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "router1.example.net"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_encrypt_passwords(self):
        params = {"encrypt_passwords": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"encrypt_passwords": False}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_configuration_template_id(self):
        params = {"configuration_template_id": [self.configuration.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_configuration_template(self):
        params = {"configuration_template": [self.configuration.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_local_autonomous_system_id(self):
        params = {"local_autonomous_system_id": [self.local_as.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_local_autonomous_system_asn(self):
        params = {"local_autonomous_system_asn": [self.local_as.asn]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_local_autonomous_system(self):
        params = {"local_autonomous_system": [self.local_as.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_status(self):
        params = {"status": [DeviceStatus.ENABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"status": [DeviceStatus.DISABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"status": [DeviceStatus.ENABLED, DeviceStatus.DISABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
