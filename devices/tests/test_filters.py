from devices.filters import PlatformFilterSet
from devices.models import Platform
from utils.testing import StandardTestCases


class PlatformTestCase(StandardTestCases.Filters):
    model = Platform
    filter = PlatformFilterSet

    @classmethod
    def setUpTestData(cls):
        Platform.objects.bulk_create(
            [
                Platform(name="Juniper Junos", slug="juniper-junos"),
                Platform(name="Cisco IOS", slug="cisco-ios"),
                Platform(name="Arista EOS", slug="arista-eos"),
            ]
        )

    def test_q(self):
        params = {"q": "Juniper"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)
        params = {"q": "cisco-ios"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)

    def test_name(self):
        params = {"name": ["Juniper Junos"]}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)
        params = {"name": ["Juniper Junos", "Cisco IOS"]}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {"slug": ["juniper-junos"]}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)
        params = {"slug": ["juniper-junos", "cisco-ios"]}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 2)
