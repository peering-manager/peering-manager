from django.conf import settings
from django.test import TestCase

from devices.models import Platform


class PlatformTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.platforms = [
            Platform(name="Juniper Junos", slug="juniper-junos"),
            Platform(name="Cisco IOS", slug="cisco-ios"),
            Platform(name="Arista EOS", slug="arista-eos"),
        ]
        Platform.objects.bulk_create(cls.platforms)
