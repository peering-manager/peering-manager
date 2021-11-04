from django.test import TestCase

from devices.filters import PlatformFilterSet
from devices.models import Platform
from utils.testing import BaseFilterSetTests


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
