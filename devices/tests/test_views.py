from devices.models import Platform
from utils.testing import ViewTestCases


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
