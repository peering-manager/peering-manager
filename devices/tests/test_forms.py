from django.test import TestCase

from peering.models import AutonomousSystem

from ..enums import *
from ..forms import *


class ConfigurationTest(TestCase):
    def test_configuration_form(self):
        test = ConfigurationForm(data={"name": "Test", "template": "test_template"})
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())


class PlatformTest(TestCase):
    def test_platform_form(self):
        test = PlatformForm(data={"name": "No Bug OS", "slug": "nobugos"})
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())


class RouterTest(TestCase):
    def test_router_form(self):
        test = RouterForm(
            data={
                "netbox_device_id": 0,
                "name": "test",
                "hostname": "test.example.com",
                "status": DeviceStatus.ENABLED,
                "local_autonomous_system": AutonomousSystem.objects.create(
                    asn=64501,
                    name="Autonomous System 1",
                    irr_as_set="AS-SET-1",
                    ipv6_max_prefixes=1,
                    ipv4_max_prefixes=0,
                    affiliated=True,
                ).pk,
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())
