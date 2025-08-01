from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from peering.models import AutonomousSystem
from utils.testing import MockedResponse

from ..models import IXAPI, ExportTemplate


class ExportTemplateTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        content_type = ContentType.objects.get_for_model(AutonomousSystem)
        cls.export_template = ExportTemplate.objects.create(
            content_type=content_type, name="Test", template="{{ dataset | length }}"
        )

    def test_render(self):
        self.assertEqual("0", self.export_template.render())


class IXAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        IXAPI.objects.bulk_create(
            [
                IXAPI(
                    name="IXP 1",
                    api_url="https://ixp1-ixapi.example.net/v1/",
                    api_key="key-ixp1",
                    api_secret="secret-ixp1",
                ),
                IXAPI(
                    name="IXP 2",
                    api_url="https://ixp2-ixapi.example.net/v2/",
                    api_key="key-ixp2",
                    api_secret="secret-ixp2",
                ),
                IXAPI(
                    name="IXP 3",
                    api_url="https://ixp3-ixapi.example.net/v3/",
                    api_key="key-ixp3",
                    api_secret="secret-ixp3",
                ),
            ]
        )
        cls.ix_api = IXAPI.objects.get(name="IXP 1")

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(
            fixture="extras/tests/fixtures/ix_api/authenticate.json"
        ),
    )
    def test_version(self, *_):
        with patch("pyixapi.core.query.Request.get_version", return_value=1):
            self.assertEqual(1, IXAPI.objects.get(name="IXP 1").version)
        with patch("pyixapi.core.query.Request.get_version", return_value=2):
            self.assertEqual(2, IXAPI.objects.get(name="IXP 2").version)
        with patch("pyixapi.core.query.Request.get_version", return_value=3):
            self.assertEqual(3, IXAPI.objects.get(name="IXP 3").version)

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(
            fixture="extras/tests/fixtures/ix_api/authenticate.json"
        ),
    )
    def test_dial(self, *_):
        a = self.ix_api.dial()
        self.assertIsNotNone(a)

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(
            fixture="extras/tests/fixtures/ix_api/authenticate.json"
        ),
    )
    def test_get_health(self, *_):
        # health endpoint not available in version 1
        with patch("pyixapi.core.query.Request.get_version", return_value=1):
            i = IXAPI.objects.get(name="IXP 1")
            self.assertEqual("", i.get_health())

        i = IXAPI.objects.get(name="IXP 2")
        with patch("pyixapi.core.query.Request.get_version", return_value=2):
            with patch(
                "requests.sessions.Session.get",
                return_value=MockedResponse(content={"status": "up"}),
            ):
                self.assertEqual("healthy", i.get_health())
            with patch(
                "requests.sessions.Session.get",
                return_value=MockedResponse(content={"status": "warn"}),
            ):
                self.assertEqual("degraded", i.get_health())
            with patch(
                "requests.sessions.Session.get",
                return_value=MockedResponse(content={"status": "error"}),
            ):
                self.assertEqual("unhealthy", i.get_health())

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(
            fixture="extras/tests/fixtures/ix_api/authenticate.json"
        ),
    )
    @patch("pyixapi.core.api.API.version", return_value=1)
    def test_get_accounts(self, *_):
        with patch(
            "requests.sessions.Session.get",
            return_value=MockedResponse(
                fixture="extras/tests/fixtures/ix_api/accounts.json"
            ),
        ):
            a = self.ix_api.get_accounts()
            self.assertEqual(2, len(a))

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(
            fixture="extras/tests/fixtures/ix_api/authenticate.json"
        ),
    )
    @patch("pyixapi.core.api.API.version", return_value=1)
    def test_get_identity(self, *_):
        with patch(
            "requests.sessions.Session.get",
            return_value=MockedResponse(content=[{"id": "1234", "name": "Customer 1"}]),
        ):
            self.assertIsNone(self.ix_api.get_identity())
            self.ix_api.identity = "1234"
            self.assertEqual("1234", self.ix_api.get_identity().id)

        # If API yields more than one account
        with patch(
            "requests.sessions.Session.get",
            fixture="extras/tests/fixtures/ix_api/accounts.json",
        ):
            self.assertIsNone(self.ix_api.get_identity())

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(
            fixture="extras/tests/fixtures/ix_api/authenticate.json"
        ),
    )
    @patch("pyixapi.core.api.API.version", return_value=1)
    def test_get_network_service_configs(self, *_):
        with patch(
            "requests.sessions.Session.get",
            side_effect=[
                MockedResponse(
                    fixture="extras/tests/fixtures/ix_api/network_service_configs.json"
                ),
                MockedResponse(
                    fixture="extras/tests/fixtures/ix_api/network_services.json"
                ),
                MockedResponse(
                    fixture="extras/tests/fixtures/ix_api/network_features.json"
                ),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/products.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/macs.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/ips.json"),
            ],
        ):
            i = self.ix_api.get_network_service_configs()
            self.assertEqual("1234", i[0].id)
            self.assertEqual("production", i[0].state)

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(
            fixture="extras/tests/fixtures/ix_api/authenticate.json"
        ),
    )
    @patch("pyixapi.core.api.API.version", return_value=1)
    def test_get_network_services(self, *_):
        with patch(
            "requests.sessions.Session.get",
            side_effect=[
                MockedResponse(
                    fixture="extras/tests/fixtures/ix_api/network_service_configs.json"
                ),
                MockedResponse(
                    fixture="extras/tests/fixtures/ix_api/network_services.json"
                ),
                MockedResponse(
                    fixture="extras/tests/fixtures/ix_api/network_features.json"
                ),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/products.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/macs.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/ips.json"),
            ],
        ):
            i = self.ix_api.get_network_services()
            self.assertEqual("1234", i[0].id)
            self.assertEqual(1234, i[0].peeringdb_ixid)
