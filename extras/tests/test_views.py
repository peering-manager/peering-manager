from unittest.mock import patch

from extras.models import IXAPI
from utils.testing import ViewTestCases


class IXAPITestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = IXAPI

    test_bulk_edit_objects = None

    @classmethod
    def setUpTestData(cls):
        IXAPI.objects.bulk_create(
            [
                IXAPI(
                    name="IXP 1",
                    url="https://ixp1-ixapi.example.net/v1/",
                    api_key="key-ixp1",
                    api_secret="secret-ixp1",
                    identity="1234",
                ),
                IXAPI(
                    name="IXP 2",
                    url="https://ixp2-ixapi.example.net/v2/",
                    api_key="key-ixp2",
                    api_secret="secret-ixp2",
                    identity="1234",
                ),
                IXAPI(
                    name="IXP 3",
                    url="https://ixp3-ixapi.example.net/v3/",
                    api_key="key-ixp3",
                    api_secret="secret-ixp3",
                    identity="1234",
                ),
            ]
        )

        cls.form_data = {
            "name": "IXP 4",
            "url": "https://ixp4-ixapi.example.net/v1/",
            "api_key": "key-ixp4",
            "api_secret": "secret-ixp4",
            "identity": "1234",
        }

    def test_get_object_anonymous(self):
        with patch(
            "extras.models.ix_api.IXAPI.get_accounts",
            return_value=[
                {"id": "1234", "name": "Account 1"},
                {"id": "5678", "name": "Account 2"},
            ],
        ):
            super().test_get_object_anonymous()

    def test_get_object_with_permission(self):
        with patch(
            "extras.models.ix_api.IXAPI.get_accounts",
            return_value=[
                {"id": "1234", "name": "Account 1"},
                {"id": "5678", "name": "Account 2"},
            ],
        ):
            super().test_get_object_with_permission()

    def test_create_object_with_permission(self):
        with patch(
            "extras.models.ix_api.IXAPI.get_accounts",
            return_value=[
                {"id": "1234", "name": "Account 1"},
                {"id": "5678", "name": "Account 2"},
            ],
        ):
            super().test_create_object_with_permission()

    def test_edit_object_with_permission(self):
        with patch(
            "extras.models.ix_api.IXAPI.get_accounts",
            return_value=[
                {"id": "1234", "name": "Account 1"},
                {"id": "5678", "name": "Account 2"},
            ],
        ):
            super().test_edit_object_with_permission()
