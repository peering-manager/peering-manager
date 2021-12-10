import ipaddress
from unittest.mock import patch

from django.test import TestCase

from extras.models import IXAPI
from utils.testing import MockedResponse


class IXAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        IXAPI.objects.bulk_create(
            [
                IXAPI(
                    name="IXP 1",
                    url="https://ixp1-ixapi.example.net/v1/",
                    api_key="key-ixp1",
                    api_secret="secret-ixp1",
                ),
                IXAPI(
                    name="IXP 2",
                    url="https://ixp2-ixapi.example.net/v2/",
                    api_key="key-ixp2",
                    api_secret="secret-ixp2",
                ),
                IXAPI(
                    name="IXP 3",
                    url="https://ixp3-ixapi.example.net/v3/",
                    api_key="key-ixp3",
                    api_secret="secret-ixp3",
                ),
            ]
        )
        cls.ix_api = IXAPI.objects.get(name="IXP 1")

    def test_version(self):
        self.assertEqual(1, IXAPI.objects.get(name="IXP 1").version)
        self.assertEqual(2, IXAPI.objects.get(name="IXP 2").version)
        self.assertEqual(3, IXAPI.objects.get(name="IXP 3").version)

    @patch(
        "requests.post",
        return_value=MockedResponse(
            content={"access_token": "1234", "refresh_token": "1234"}
        ),
    )
    def test_dial(self, *_):
        c = self.ix_api.dial()
        self.assertEqual("1234", c.access_token)
        self.assertEqual("1234", c.refresh_token)

    @patch(
        "requests.post",
        return_value=MockedResponse(
            content={"access_token": "1234", "refresh_token": "1234"}
        ),
    )
    def test_get_health(self, *_):
        with self.assertRaises(NotImplementedError):
            self.ix_api.get_health()

        i = IXAPI.objects.get(name="IXP 2")
        with patch(
            "requests.get", return_value=MockedResponse(content={"status": "up"})
        ):
            self.assertEqual("healthy", i.get_health())
        with patch(
            "requests.get", return_value=MockedResponse(content={"status": "warn"})
        ):
            self.assertEqual("degraded", i.get_health())
        with patch(
            "requests.get", return_value=MockedResponse(content={"status": "error"})
        ):
            self.assertEqual("unhealthy", i.get_health())

    @patch(
        "requests.post",
        return_value=MockedResponse(
            content={"access_token": "1234", "refresh_token": "1234"}
        ),
    )
    def test_get_customers(self, *_):
        with patch(
            "requests.get",
            return_value=MockedResponse(
                fixture="extras/tests/fixtures/ix_api/customers.json"
            ),
        ):
            c = self.ix_api.get_customers()
            self.assertEqual(2, len(c))
            self.assertEqual("1234", c[0]["id"])
            self.assertEqual("5678", c[1]["id"])

    @patch(
        "requests.post",
        return_value=MockedResponse(
            content={"access_token": "1234", "refresh_token": "1234"}
        ),
    )
    def test_get_identity(self, *_):
        with patch(
            "requests.get",
            return_value=MockedResponse(content=[{"id": "1234", "name": "Customer 1"}]),
        ):
            self.assertIsNone(self.ix_api.get_identity())
            self.ix_api.identity = "1234"
            self.assertEqual("1234", self.ix_api.get_identity()["id"])

    @patch(
        "requests.post",
        return_value=MockedResponse(
            content={"access_token": "1234", "refresh_token": "1234"}
        ),
    )
    def test_get_ips(self, *_):
        with patch(
            "requests.get",
            return_value=MockedResponse(
                fixture="extras/tests/fixtures/ix_api/ips.json"
            ),
        ):
            i = self.ix_api.get_ips()
            self.assertEqual("1234", i[0].id)
            self.assertEqual("5678", i[1].id)
            self.assertIsInstance(i[0].network, ipaddress.IPv6Network)
            self.assertIsInstance(i[1].network, ipaddress.IPv4Network)
            self.assertIsInstance(i[0].address, ipaddress.IPv6Address)
            self.assertIsInstance(i[1].address, ipaddress.IPv4Address)

    @patch(
        "requests.post",
        return_value=MockedResponse(
            content={"access_token": "1234", "refresh_token": "1234"}
        ),
    )
    def test_get_macs(self, *_):
        with patch(
            "requests.get",
            return_value=MockedResponse(
                fixture="extras/tests/fixtures/ix_api/macs.json"
            ),
        ):
            i = self.ix_api.get_macs()
            self.assertEqual("1234", i[0].id)
            self.assertEqual("AA:BB:CC:DD:EE:FF", i[0].address)

    @patch(
        "requests.post",
        return_value=MockedResponse(
            content={"access_token": "1234", "refresh_token": "1234"}
        ),
    )
    def test_get_network_features(self, *_):
        with patch(
            "requests.get",
            return_value=MockedResponse(
                fixture="extras/tests/fixtures/ix_api/network_features.json"
            ),
        ):
            i = self.ix_api.get_network_features()
            self.assertEqual("1234", i[0].id)
            self.assertEqual(64500, i[0].asn)
            self.assertTrue(i[0].required)

    @patch(
        "requests.post",
        return_value=MockedResponse(
            content={"access_token": "1234", "refresh_token": "1234"}
        ),
    )
    def test_get_network_service_configs(self, *_):
        with patch(
            "requests.get",
            return_value=MockedResponse(
                fixture="extras/tests/fixtures/ix_api/network_service_configs.json"
            ),
        ):
            i = self.ix_api.get_network_service_configs()
            self.assertEqual("1234", i[0].id)
            self.assertEqual("production", i[0].state)

    @patch(
        "requests.post",
        return_value=MockedResponse(
            content={"access_token": "1234", "refresh_token": "1234"}
        ),
    )
    def test_get_network_services(self, *_):
        with patch(
            "requests.get",
            return_value=MockedResponse(
                fixture="extras/tests/fixtures/ix_api/network_services.json"
            ),
        ):
            i = self.ix_api.get_network_services()
            self.assertEqual("1234", i[0].id)
            self.assertEqual(1234, i[0].peeringdb_ixid)

    @patch(
        "requests.post",
        return_value=MockedResponse(
            content={"access_token": "1234", "refresh_token": "1234"}
        ),
    )
    def test_get_products(self, *_):
        with patch(
            "requests.get",
            return_value=MockedResponse(
                fixture="extras/tests/fixtures/ix_api/products.json"
            ),
        ):
            self.assertEqual("1234", self.ix_api.get_products()[0]["id"])
