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
