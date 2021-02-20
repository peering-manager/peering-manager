from devices.models import Platform
from utils.testing import StandardTestCases


class PlatformTestCase(StandardTestCases.Views):
    model = Platform

    test_get_object = None
    test_bulk_edit_objects = None

    @classmethod
    def setUpTestData(cls):
        Platform.objects.bulk_create(
            [
                Platform(name="Juniper Junos", slug="juniper-junos"),
                Platform(name="Cisco IOS", slug="cisco-ios"),
                Platform(name="Arista EOS", slug="arista-eos"),
            ]
        )

        cls.form_data = {
            "name": "Cisco IOS-XR",
            "slug": "cisco-ios-xr",
            "napalm_driver": "iosxr",
            "napalm_args": {},
            "description": "",
        }
