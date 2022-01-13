from devices.models import Configuration, Platform
from utils.testing import ViewTestCases


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
