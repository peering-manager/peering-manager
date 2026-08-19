from unittest.mock import PropertyMock, patch

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.test import TestCase

from net.models import Connection
from peering.models import AutonomousSystem, InternetExchange
from utils.testing import MockedResponse

from ..models import IXAPI, ExportTemplate, TableConfig


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
        return_value=MockedResponse(fixture="extras/tests/fixtures/ix_api/authenticate.json"),
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
        return_value=MockedResponse(fixture="extras/tests/fixtures/ix_api/authenticate.json"),
    )
    def test_dial(self, *_):
        a = self.ix_api.dial()
        self.assertIsNotNone(a)

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(fixture="extras/tests/fixtures/ix_api/authenticate.json"),
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
        return_value=MockedResponse(fixture="extras/tests/fixtures/ix_api/authenticate.json"),
    )
    @patch("pyixapi.core.api.API.version", return_value=1)
    def test_get_accounts(self, *_):
        with patch(
            "requests.sessions.Session.get",
            return_value=MockedResponse(fixture="extras/tests/fixtures/ix_api/accounts.json"),
        ):
            a = self.ix_api.get_accounts()
            self.assertEqual(2, len(a))

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(fixture="extras/tests/fixtures/ix_api/authenticate.json"),
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
            return_value=MockedResponse(fixture="extras/tests/fixtures/ix_api/accounts.json"),
        ):
            self.assertIsNone(self.ix_api.get_identity())

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(fixture="extras/tests/fixtures/ix_api/authenticate.json"),
    )
    @patch("pyixapi.core.api.API.version", return_value=1)
    def test_get_network_service_configs(self, *_):
        with patch(
            "requests.sessions.Session.get",
            side_effect=[
                MockedResponse(fixture="extras/tests/fixtures/ix_api/network_service_configs.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/network_services.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/network_features.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/products.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/macs.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/ips.json"),
            ],
        ):
            i = self.ix_api.get_network_service_configs()
            self.assertEqual("1234", i[0].id)
            self.assertEqual("production", i[0].state)

    def test_get_account_dict(self):
        self.ix_api.identity = "1234"

        with patch("extras.models.ixapi.IXAPI.version", new_callable=PropertyMock, return_value=1):
            self.assertEqual(
                {"managing_customer": "1234", "consuming_customer": "1234"}, self.ix_api.get_account_dict()
            )
        with patch("extras.models.ixapi.IXAPI.version", new_callable=PropertyMock, return_value=2):
            self.assertEqual({"managing_account": "1234", "consuming_account": "1234"}, self.ix_api.get_account_dict())

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(fixture="extras/tests/fixtures/ix_api/authenticate.json"),
    )
    @patch("pyixapi.core.api.API.version", return_value=1)
    def test_get_network_services(self, *_):
        with patch(
            "requests.sessions.Session.get",
            side_effect=[
                MockedResponse(fixture="extras/tests/fixtures/ix_api/network_service_configs.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/network_services.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/network_features.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/products.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/macs.json"),
                MockedResponse(fixture="extras/tests/fixtures/ix_api/ips.json"),
            ],
        ):
            i = self.ix_api.get_network_services()
            self.assertEqual("1234", i[0].id)
            self.assertEqual(1234, i[0].peeringdb_ixid)


class TableConfigTest(TestCase):
    def test_columns(self):
        columns = ["asn", "name", "irr_as_set"]
        TableConfig.objects.create(table="AutonomousSystemTable", columns=columns)

        config = TableConfig.objects.get(table="AutonomousSystemTable")
        self.assertEqual(columns, config.columns)


IXAPI_DATA = {
    "network_service_configs": [
        {
            "id": "nsc-1",
            "state": "production",
            "type": "exchange_lan",
            "network_service": "ns-1",
            "connection": "ixapi-conn-1",
            "ips": ["ip-v6", "ip-v4"],
            "macs": ["mac-1"],
            "outer_vlan": 100,
            "inner_vlan": None,
        },
        {
            "id": "nsc-2",
            "state": "archived",
            "network_service": "ns-1",
            "connection": "ixapi-conn-2",
            "ips": [],
            "macs": [],
        },
    ],
    "network_services": [
        {
            "id": "ns-1",
            "name": "Peering LAN",
            "type": "exchange_lan",
            "product": "po-1",
            "ips": ["ip-v6", "ip-v4"],
            "network_features": ["nf-1"],
            "peeringdb_ixid": 42,
        }
    ],
    "network_features": [
        {"id": "nf-1", "name": "Route Server", "type": "route_server", "asn": 64500, "required": True}
    ],
    "product_offerings": [{"id": "po-1", "name": "IXP Nowhere"}],
    "macs": [{"id": "mac-1", "address": "AA:BB:CC:DD:EE:FF"}],
    "ips": [
        {"id": "ip-v6", "address": "2001:db8::1", "prefix_length": 64},
        {"id": "ip-v4", "address": "192.0.2.1", "prefix_length": 24},
    ],
}


class IXAPIDataResolutionTest(TestCase):
    """
    Resolution of the cached IX-API payload, without any call to the remote API.
    """

    @classmethod
    def setUpTestData(cls):
        cls.ix_api = IXAPI.objects.create(
            name="IXP",
            api_url="https://ixp-ixapi.example.net/v2/",
            api_key="key",
            api_secret="secret",
            identity="1234",
        )
        cls.local_autonomous_system = AutonomousSystem.objects.create(asn=201281, name="Test", affiliated=True)
        cls.internet_exchange_point = InternetExchange.objects.create(
            name="Test",
            slug="test",
            local_autonomous_system=cls.local_autonomous_system,
            ixapi_endpoint=cls.ix_api,
        )
        # Prefix lengths differ from the ones IX-API reports on purpose
        cls.connection = Connection.objects.create(
            internet_exchange_point=cls.internet_exchange_point,
            ipv6_address="2001:db8::1/126",
            ipv4_address="192.0.2.1/26",
            mac_address="aa:bb:cc:dd:ee:ff",
        )

    def setUp(self):
        self.ix_api.invalidate_cache()
        cache.set(self.ix_api._cache_key, IXAPI_DATA)
        self.addCleanup(self.ix_api.invalidate_cache)

    def test_get_network_service_configs(self):
        configs = self.ix_api.get_network_service_configs()

        # The archived config is left out
        self.assertEqual(1, len(configs))
        config = configs[0]

        self.assertEqual("nsc-1", config.id)
        self.assertEqual("production", config.state)
        self.assertEqual(100, config.outer_vlan)
        self.assertEqual(["aa:bb:cc:dd:ee:ff"], config.macs)
        self.assertEqual(
            ["2001:db8::1/64", "192.0.2.1/24"],
            [str(i) for i in config.ips],
        )
        self.assertEqual("2001:db8::1/64", str(config.ipv6_address))
        self.assertEqual("192.0.2.1/24", str(config.ipv4_address))

        # A different prefix length must not prevent the match
        self.assertEqual(self.connection, config.connection)

        # The IX-API record itself is never modified
        self.assertEqual(["ip-v6", "ip-v4"], config.record.get("ips"))
        self.assertEqual(["mac-1"], config.record.get("macs"))
        self.assertEqual("ixapi-conn-1", config.record.get("connection"))

    def test_get_network_service_configs_matches_single_stack(self):
        self.connection.ipv4_address = None
        self.connection.save()

        config = self.ix_api.get_network_service_configs()[0]
        self.assertEqual(self.connection, config.connection)

    def test_get_network_services(self):
        services = self.ix_api.get_network_services()

        self.assertEqual(1, len(services))
        service = services[0]

        self.assertEqual("ns-1", service.id)
        self.assertEqual("IXP Nowhere", service.product_offering.name)
        self.assertEqual(["Route Server"], [f.name for f in service.network_features])
        self.assertEqual("2001:db8::/64", str(service.subnet_v6))
        self.assertEqual("192.0.2.0/24", str(service.subnet_v4))
        self.assertEqual(["nsc-1"], [c.id for c in service.network_service_configs])

    def test_get_ixapi_network_service(self):
        service = self.internet_exchange_point.get_ixapi_network_service()
        self.assertEqual("ns-1", service.id)

    def test_get_ixapi_network_service_with_single_stack_connection(self):
        self.connection.ipv4_address = None
        self.connection.save()

        service = self.internet_exchange_point.get_ixapi_network_service()
        self.assertEqual("ns-1", service.id)

    def test_connection_network_service_config(self):
        config = self.connection.ixapi_network_service_config()

        self.assertEqual("nsc-1", config.id)
        self.assertEqual("aa:bb:cc:dd:ee:ff", self.connection.ixapi_mac_address(config))

    def test_connection_network_service_config_survives_an_api_failure(self):
        self.ix_api.invalidate_cache()
        with patch("extras.models.ixapi.IXAPI.dial", side_effect=OSError("ix-api is down")):
            self.assertIsNone(self.connection.ixapi_network_service_config())

    def test_create_mac_address_reuses_a_known_one(self):
        with patch("extras.models.ixapi.IXAPI.dial") as dial:
            mac = self.ix_api.create_mac_address("aa:bb:cc:dd:ee:ff")

        dial.assert_not_called()
        self.assertEqual("mac-1", mac.id)
        self.assertEqual("aa:bb:cc:dd:ee:ff", mac.address)

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(fixture="extras/tests/fixtures/ix_api/authenticate.json"),
    )
    def test_set_ixapi_mac_address(self, *_):
        stored = IXAPI_DATA["network_service_configs"][0] | {"macs": ["mac-old"]}
        record = MockedResponse(content=stored)

        with (
            patch("requests.sessions.Session.get", return_value=record),
            patch("requests.sessions.Session.patch", return_value=record) as patch_call,
        ):
            self.assertTrue(self.connection.set_ixapi_mac_address())

        # Only the MAC addresses are sent back, as their IX-API identifiers
        self.assertEqual({"macs": ["mac-1"]}, patch_call.call_args.kwargs["json"])

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(fixture="extras/tests/fixtures/ix_api/authenticate.json"),
    )
    def test_set_ixapi_mac_address_already_set(self, *_):
        record = MockedResponse(content=IXAPI_DATA["network_service_configs"][0])

        with (
            patch("requests.sessions.Session.get", return_value=record),
            patch("requests.sessions.Session.patch") as patch_call,
        ):
            self.assertTrue(self.connection.set_ixapi_mac_address())

        patch_call.assert_not_called()
