from django.test import TestCase

from utils.testing import BaseFilterSetTests

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
