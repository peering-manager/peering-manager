import ipaddress

from django.conf import settings
from django.test import TestCase
from unittest.mock import patch

from peering.enums import BGPRelationship, CommunityType, Platform, RoutingPolicyType
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    Configuration,
    DirectPeeringSession,
    Email,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from peering.tests.mocked_data import *
from utils.crypto.cisco import (
    decrypt as cisco_decrypt,
    is_encrypted as cisco_is_encrypted,
)
from utils.crypto.junos import (
    decrypt as junos_decrypt,
    is_encrypted as junos_is_encrypted,
)
from utils.testing import json_file_to_python_type, MockedResponse


def mocked_peeringdb(*args, **kwargs):
    if "asn" in kwargs["params"] and kwargs["params"]["asn"] == 65536:
        return MockedResponse(fixture="peeringdb/tests/fixtures/as65536.json")

    return MockedResponse(status_code=404)


class AutonomousSystemTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.autonomous_system = AutonomousSystem.objects.create(
            asn=65537, name="Test", irr_as_set="AS-MOCKED"
        )

    @patch("peeringdb.http.requests.get", side_effect=mocked_peeringdb)
    def test_create_from_peeringdb(self, *_):
        asn = 65536

        # Illegal ASN
        self.assertIsNone(AutonomousSystem.create_from_peeringdb(64500))

        # Create the AS
        a_s = AutonomousSystem.create_from_peeringdb(asn)
        self.assertIsNotNone(a_s)
        self.assertEqual(asn, a_s.asn)

        exists = True
        try:
            AutonomousSystem.objects.get(asn=asn)
        except AutonomousSystem.DoesNotExist:
            exists = False
        self.assertTrue(exists)

        # Trying to re-create the AS should just return it
        a_s = AutonomousSystem.create_from_peeringdb(asn)
        self.assertIsNotNone(a_s)
        self.assertEqual(asn, a_s.asn)

        exists = True
        try:
            AutonomousSystem.objects.get(asn=asn)
        except (
            AutonomousSystem.DoesNotExist,
            AutonomousSystem.MultipleObjectsReturned,
        ):
            exists = False
        self.assertTrue(exists)

    @patch("peeringdb.http.requests.get", side_effect=mocked_peeringdb)
    def test_synchronize_with_peeringdb(self, *_):
        # Create legal AS to sync with PeeringDB
        asn = 65536
        a_s = AutonomousSystem.create_from_peeringdb(asn)
        self.assertEqual(asn, a_s.asn)
        self.assertTrue(a_s.synchronize_with_peeringdb())

        # Create illegal AS to fail sync with PeeringDB
        asn = 64500
        a_s = AutonomousSystem.objects.create(asn=asn, name="Test")
        self.assertEqual(asn, a_s.asn)
        self.assertFalse(a_s.synchronize_with_peeringdb())

    def test_retrieve_irr_as_set_prefixes(self):
        with patch("peering.subprocess.Popen", side_effect=mocked_subprocess_popen):
            prefixes = self.autonomous_system.retrieve_irr_as_set_prefixes()
            self.assertEqual(1, len(prefixes["ipv6"]))
            self.assertEqual(1, len(prefixes["ipv4"]))

        with patch("peering.subprocess.Popen", side_effect=mocked_subprocess_popen):
            self.autonomous_system.irr_as_set = "AS-ERROR"
            prefixes = self.autonomous_system.retrieve_irr_as_set_prefixes()
            self.assertEqual(1, len(prefixes["ipv6"]))
            self.assertEqual(1, len(prefixes["ipv4"]))

    def test_get_irr_as_set_prefixes(self):
        with patch("peering.subprocess.Popen", side_effect=mocked_subprocess_popen):
            self.autonomous_system.prefixes = (
                self.autonomous_system.retrieve_irr_as_set_prefixes()
            )
            self.assertEqual(1, len(self.autonomous_system.prefixes["ipv6"]))
            self.assertEqual(1, len(self.autonomous_system.prefixes["ipv4"]))

        prefixes = self.autonomous_system.get_irr_as_set_prefixes()
        self.assertEqual(self.autonomous_system.prefixes["ipv6"], prefixes["ipv6"])
        self.assertEqual(self.autonomous_system.prefixes["ipv4"], prefixes["ipv4"])

    def test_get_peeringdb_network(self):
        self.assertIsNone(self.autonomous_system.get_peeringdb_network())

    def test__str__(self):
        self.assertEqual(
            f"AS{self.autonomous_system.asn} - {self.autonomous_system.name}",
            str(self.autonomous_system),
        )


class CommunityTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.communities = [
            Community(
                name="test-1",
                slug="test-1",
                value="64500:1",
                type=CommunityType.EGRESS,
            ),
            Community(
                name="test-2",
                slug="test-2",
                value="64500:2",
                type=CommunityType.INGRESS,
            ),
            Community(name="test-3", slug="test-3", value="64500:3", type="unknown"),
        ]
        Community.objects.bulk_create(cls.communities)

    def test_get_type_html(self):
        expected = [
            '<span class="badge badge-primary">Egress</span>',
            '<span class="badge badge-info">Ingress</span>',
            '<span class="badge badge-secondary">Unknown</span>',
        ]

        for i in range(len(expected)):
            self.assertEqual(expected[i], self.communities[i].get_type_html())


class ConfigurationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.template = Configuration.objects.create(name="Test", template="{{ test }}")

    def test_render(self):
        self.assertEqual(self.template.render({"test": "test"}), "test")

    def test_render_preview(self):
        self.assertEqual(self.template.render_preview(), "")


class DirectPeeringSessionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.autonomous_system = AutonomousSystem.objects.create(asn=64501, name="Test")
        cls.group = BGPGroup.objects.create(
            name="Test Group", slug="testgroup", check_bgp_session_states=True
        )
        cls.router = Router.objects.create(
            name="Test",
            hostname="test.example.com",
            platform=Platform.JUNOS,
            local_autonomous_system=AutonomousSystem.objects.create(
                asn=64500,
                name="Autonomous System",
                affiliated=True,
            ),
        )
        cls.session = DirectPeeringSession.objects.create(
            autonomous_system=cls.autonomous_system,
            bgp_group=cls.group,
            ip_address="2001:db8::1",
            password="mypassword",
            router=cls.router,
        )

    def test_encrypt_password(self):
        self.assertIsNotNone(self.session.password)
        self.assertIsNone(self.session.encrypted_password)

        # Encrypt the password
        self.session.encrypt_password(self.router.platform)
        self.assertIsNotNone(self.session.encrypted_password)
        self.assertTrue(junos_is_encrypted(self.session.encrypted_password))
        self.assertEqual(
            self.session.password, junos_decrypt(self.session.encrypted_password)
        )

        # Change router platform and re-encrypt
        self.router.platform = Platform.IOSXR
        self.session.encrypt_password(self.router.platform)
        self.assertIsNotNone(self.session.encrypted_password)
        self.assertTrue(cisco_is_encrypted(self.session.encrypted_password))
        self.assertEqual(
            self.session.password, cisco_decrypt(self.session.encrypted_password)
        )

        # Change router platform to an unsupported one
        self.router.platform = Platform.NONE
        self.session.encrypt_password(self.router.platform)
        self.assertIsNone(self.session.encrypted_password)

        # Change password to None
        self.session.password = None
        self.router.platform = Platform.JUNOS
        self.session.encrypt_password(self.router.platform)
        self.assertIsNone(self.session.encrypted_password)

        # Change the password to a new one and make sure it changes the encrypted one
        self.session.password = "mypassword1"
        self.session.encrypt_password(self.router.platform)
        self.assertEqual(
            self.session.password, junos_decrypt(self.session.encrypted_password)
        )
        self.session.password = "mypassword2"
        self.session.encrypt_password(self.router.platform)
        self.assertEqual(
            self.session.password, junos_decrypt(self.session.encrypted_password)
        )

    def test_poll(self):
        with patch(
            "peering.models.Router.get_bgp_neighbors_detail",
            return_value=self.router.find_bgp_neighbor_detail(
                json_file_to_python_type(
                    "peering/tests/fixtures/get_bgp_neighbors_detail.json"
                ),
                "2001:db8::1",
            ),
        ):
            self.assertTrue(self.session.poll())
            self.assertEqual(567_257, self.session.received_prefix_count)


class EmailTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.email = Email.objects.create(
            name="Test", subject="{{ test }}", template="{{ test }}"
        )

    def test_render(self):
        self.assertEqual(self.email.render({"test": "test"}), ("test", "test"))

    def test_render_preview(self):
        self.assertEqual(self.email.render_preview(), ("", ""))


class InternetExchangeTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.internet_exchange = InternetExchange.objects.create(
            name="Test", slug="test"
        )

    def test_is_peeringdb_valid(self):
        # Not linked with PeeringDB but considered as valid
        self.assertTrue(self.internet_exchange.is_peeringdb_valid())

        # Set invalid ID, must result in false
        self.internet_exchange.peeringdb_id = 14658
        self.internet_exchange.save()
        self.assertFalse(self.internet_exchange.is_peeringdb_valid())

        # Set valid ID, must result in true
        self.internet_exchange.peeringdb_id = 29146
        self.internet_exchange.save()
        self.assertTrue(self.internet_exchange.is_peeringdb_valid())

    def test_get_peeringdb_id(self):
        # Expected results
        expected = [0, 0, 0, 0, 29146, 29146, 29146]

        # Test data
        data = [
            {
                # No IP addresses
            },
            {"ipv6_address": "2001:db8::1"},
            {"ipv4_address": "198.51.100.1"},
            {"ipv6_address": "2001:db8::1", "ipv4_address": "198.51.100.1"},
            {"ipv6_address": "2001:7f8:1::a502:9467:1"},
            {"ipv4_address": "80.249.210.208"},
            {
                "ipv6_address": "2001:7f8:1::a502:9467:1",
                "ipv4_address": "80.249.210.208",
            },
        ]

        # Run test cases
        for i in range(len(expected)):
            ixp = InternetExchange.objects.create(
                name="Test {}".format(i), slug="test_{}".format(i), **data[i]
            )
            self.assertEqual(expected[i], ixp.get_peeringdb_id())

    def test_import_peering_sessions(self):
        # Expected results
        expected = [
            # First case
            (1, 1, []),
            # Second case
            (0, 1, []),
            # Third case
            (0, 1, []),
            # Fourth case
            (0, 0, []),
        ]

        session_lists = [
            # First case, one new session with one new AS
            [{"ip_address": ipaddress.ip_address("2001:db8::1"), "remote_asn": 201281}],
            # Second case, one new session with one known AS
            [{"ip_address": ipaddress.ip_address("192.0.2.1"), "remote_asn": 201281}],
            # Third case, new IPv4 session on another IX but with an IP that
            # has already been used
            [{"ip_address": ipaddress.ip_address("192.0.2.1"), "remote_asn": 201281}],
            # Fourth case, new IPv4 session with IPv6 prefix
            [{"ip_address": ipaddress.ip_address("203.0.113.1"), "remote_asn": 201281}],
        ]

        prefix_lists = [
            # First case
            [ipaddress.ip_network("2001:db8::/64")],
            # Second case
            [ipaddress.ip_network("192.0.2.0/24")],
            # Third case
            [ipaddress.ip_network("192.0.2.0/24")],
            # Fourth case
            [ipaddress.ip_network("2001:db8::/64")],
        ]

        # Run test cases
        for i in range(len(expected)):
            ixp = InternetExchange.objects.create(
                name="Test {}".format(i), slug="test_{}".format(i)
            )
            self.assertEqual(
                expected[i],
                ixp._import_peering_sessions(session_lists[i], prefix_lists[i]),
            )
            self.assertEqual(expected[i][1], len(ixp.get_peering_sessions()))


class InternetExchangePeeringSessionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a_s = AutonomousSystem.objects.create(asn=64510, name="Test")
        cls.router = Router.objects.create(
            name="Test",
            hostname="test.example.com",
            platform=Platform.JUNOS,
            local_autonomous_system=AutonomousSystem.objects.create(
                asn=64500,
                name="Autonomous System",
                affiliated=True,
            ),
        )
        cls.ix = InternetExchange.objects.create(
            name="Test Group",
            slug="testgroup",
            ipv6_address="2001:db8::1337",
            ipv4_address="192.0.2.64",
            router=cls.router,
            check_bgp_session_states=True,
        )
        cls.session = InternetExchangePeeringSession.objects.create(
            autonomous_system=cls.a_s,
            internet_exchange=cls.ix,
            ip_address="2001:db8::1",
            password="mypassword",
        )

    def test_encrypt_password(self):
        self.session.password = "mypassword"
        self.assertIsNotNone(self.session.password)
        self.assertIsNone(self.session.encrypted_password)

        # Encrypt the password
        self.session.encrypt_password(self.router.platform)
        self.assertIsNotNone(self.session.encrypted_password)
        self.assertTrue(junos_is_encrypted(self.session.encrypted_password))
        self.assertEqual(
            self.session.password, junos_decrypt(self.session.encrypted_password)
        )

        # Change router platform and re-encrypt
        self.router.platform = Platform.IOSXR
        self.session.encrypt_password(self.router.platform)
        self.assertIsNotNone(self.session.encrypted_password)
        self.assertTrue(cisco_is_encrypted(self.session.encrypted_password))
        self.assertEqual(
            self.session.password, cisco_decrypt(self.session.encrypted_password)
        )

        # Change router platform to an unsupported one
        self.router.platform = Platform.NONE
        self.session.encrypt_password(self.router.platform)
        self.assertIsNone(self.session.encrypted_password)

        # Change password to None and
        self.session.password = None
        self.router.platform = Platform.JUNOS
        self.session.encrypt_password(self.router.platform)
        self.assertIsNone(self.session.encrypted_password)

    def test_exists_in_peeringdb(self):
        self.assertFalse(self.session.exists_in_peeringdb())

    def test_is_abandoned(self):
        self.assertFalse(self.session.is_abandoned())

    def test_poll(self):
        with patch(
            "peering.models.Router.get_bgp_neighbors_detail",
            return_value=self.router.find_bgp_neighbor_detail(
                json_file_to_python_type(
                    "peering/tests/fixtures/get_bgp_neighbors_detail.json"
                ),
                "2001:db8::1",
            ),
        ):
            self.assertTrue(self.session.poll())
            self.assertEqual(567_257, self.session.received_prefix_count)


class RouterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.local_as = AutonomousSystem.objects.create(
            asn=64500,
            name="Autonomous System",
            affiliated=True,
        )
        cls.bgp_neighbors_detail = json_file_to_python_type(
            "peering/tests/fixtures/get_bgp_neighbors_detail.json"
        )
        cls.router = Router.objects.create(
            name="Test",
            hostname="test.example.com",
            platform=Platform.JUNOS,
            local_autonomous_system=cls.local_as,
        )

    def test_get_configuration_context(self):
        for i in range(1, 6):
            AutonomousSystem.objects.create(asn=i, name=f"Test {i}")
        bgp_group = BGPGroup.objects.create(name="Test Group", slug="testgroup")
        for i in range(1, 6):
            DirectPeeringSession.objects.create(
                local_ip_address="192.0.2.1",
                autonomous_system=AutonomousSystem.objects.get(asn=i),
                bgp_group=bgp_group,
                relationship=BGPRelationship.PRIVATE_PEERING,
                ip_address=f"10.0.0.{i}",
                enabled=bool(i % 2),
                router=self.router,
            )
        internet_exchange = InternetExchange.objects.create(
            name="Test IX", slug="testix", router=self.router
        )
        for i in range(1, 6):
            InternetExchangePeeringSession.objects.create(
                autonomous_system=AutonomousSystem.objects.get(asn=i),
                internet_exchange=internet_exchange,
                ip_address=f"2001:db8::{i}",
                enabled=bool(i % 2),
            )
            InternetExchangePeeringSession.objects.create(
                autonomous_system=AutonomousSystem.objects.get(asn=i),
                internet_exchange=internet_exchange,
                ip_address=f"192.0.2.{i}",
                enabled=bool(i % 2),
            )

        # Convert to dict and merge values
        bgp_group_dict = bgp_group.to_dict()
        bgp_group_dict.update(
            {
                "sessions": {
                    6: [
                        session.to_dict()
                        for session in DirectPeeringSession.objects.filter(
                            ip_address__family=6
                        )
                    ],
                    4: [
                        session.to_dict()
                        for session in DirectPeeringSession.objects.filter(
                            ip_address__family=4
                        )
                    ],
                }
            }
        )
        internet_exchange_dict = internet_exchange.to_dict()
        internet_exchange_dict.update(
            {
                "sessions": {
                    6: [
                        session.to_dict()
                        for session in InternetExchangePeeringSession.objects.filter(
                            ip_address__family=6
                        )
                    ],
                    4: [
                        session.to_dict()
                        for session in InternetExchangePeeringSession.objects.filter(
                            ip_address__family=4
                        )
                    ],
                }
            }
        )

        # Generate expected result
        expected = {
            "my_as": self.local_as.to_dict(),
            "autonomous_systems": [
                autonomous_system.to_dict()
                for autonomous_system in AutonomousSystem.objects.exclude(
                    pk=self.local_as.pk
                )
            ],
            "bgp_groups": [bgp_group_dict],
            "internet_exchanges": [internet_exchange_dict],
            "routing_policies": [],
            "communities": [],
        }

        result = self.router.get_configuration_context()
        self.assertEqual(result, expected)

    def test_napalm_bgp_neighbors_to_peer_list(self):
        # Expected results
        expected = [0, 0, 1, 2, 3, 2, 2]

        napalm_dicts_list = [
            # If None or empty dict passed, returned value must be empty list
            None,
            {},
            # List size must match peers number including VRFs
            {"global": {"peers": {"192.0.2.1": {"remote_as": 64500}}}},
            {
                "global": {"peers": {"192.0.2.1": {"remote_as": 64500}}},
                "vrf": {"peers": {"198.51.100.1": {"remote_as": 64501}}},
            },
            {
                "global": {"peers": {"192.0.2.1": {"remote_as": 64500}}},
                "vrf0": {"peers": {"198.51.100.1": {"remote_as": 64501}}},
                "vrf1": {"peers": {"203.0.113.1": {"remote_as": 64502}}},
            },
            # If peer does not have remote_as field, it must be ignored
            {
                "global": {"peers": {"192.0.2.1": {"remote_as": 64500}}},
                "vrf0": {"peers": {"198.51.100.1": {"remote_as": 64501}}},
                "vrf1": {"peers": {"203.0.113.1": {"not_valid": 64502}}},
            },
            # If an IP address appears more than one time, only the first
            # occurence  must be retained
            {
                "global": {"peers": {"192.0.2.1": {"remote_as": 64500}}},
                "vrf0": {"peers": {"198.51.100.1": {"remote_as": 64501}}},
                "vrf1": {"peers": {"198.51.100.1": {"remote_as": 64502}}},
            },
        ]

        # Create a router
        router = Router.objects.create(
            name="test",
            hostname="test.example.com",
            platform=Platform.JUNOS,
            local_autonomous_system=AutonomousSystem.objects.create(
                asn=64510,
                name="Autonomous System",
                affiliated=True,
            ),
        )

        # Run test cases
        for i in range(len(expected)):
            self.assertEqual(
                expected[i],
                len(router._napalm_bgp_neighbors_to_peer_list(napalm_dicts_list[i])),
            )

    def test_bgp_neighbors_detail_as_list(self):
        expected = [
            {
                "multipath": False,
                "previous_connection_state": "OpenConfirm",
                "configured_keepalive": 30,
                "messages_queued_out": 0,
                "routing_table": "global",
                "keepalive": 30,
                "input_messages": 26_006_050,
                "remove_private_as": False,
                "configured_holdtime": 0,
                "suppress_4byte_as": False,
                "suppressed_prefix_count": 0,
                "local_address": "192.0.2.2",
                "remote_address": "192.0.2.1",
                "input_updates": 25_604_153,
                "multihop": False,
                "export_policy": "",
                "remote_port": 54687,
                "local_port": 179,
                "active_prefix_count": 37358,
                "output_messages": 383_524,
                "import_policy": "",
                "connection_state": "Established",
                "received_prefix_count": 567_162,
                "local_as": 64510,
                "accepted_prefix_count": 566_998,
                "router_id": "172.17.17.1",
                "flap_count": 0,
                "last_event": "RecvKeepAlive",
                "holdtime": 90,
                "local_as_prepend": True,
                "up": True,
                "remote_as": 64500,
                "local_address_configured": False,
                "advertised_prefix_count": 111,
                "output_updates": 524,
            },
            {
                "multipath": False,
                "previous_connection_state": "EstabSync",
                "configured_keepalive": 30,
                "messages_queued_out": 0,
                "routing_table": "global",
                "keepalive": 30,
                "input_messages": 12_094_123,
                "remove_private_as": False,
                "configured_holdtime": 0,
                "suppress_4byte_as": False,
                "suppressed_prefix_count": 0,
                "local_address": "2001:db8::2",
                "remote_address": "2001:db8::1",
                "input_updates": 11_951_665,
                "multihop": False,
                "export_policy": "",
                "remote_port": 50877,
                "local_port": 179,
                "active_prefix_count": 101_545,
                "output_messages": 141_052,
                "import_policy": "",
                "connection_state": "Established",
                "received_prefix_count": 567_257,
                "local_as": 64510,
                "accepted_prefix_count": 567_257,
                "router_id": "192.168.100.1",
                "flap_count": 2,
                "last_event": "RecvKeepAlive",
                "holdtime": 90,
                "local_as_prepend": True,
                "up": True,
                "remote_as": 64501,
                "local_address_configured": False,
                "advertised_prefix_count": 111,
                "output_updates": 158,
            },
        ]

        self.assertEqual(
            expected,
            self.router.bgp_neighbors_detail_as_list(self.bgp_neighbors_detail),
        )

    def test_find_bgp_neighbor_detail(self):
        self.assertIsNone(
            self.router.find_bgp_neighbor_detail(
                self.bgp_neighbors_detail, "192.0.2.250"
            )
        )
        self.assertIsNone(
            self.router.find_bgp_neighbor_detail(
                self.bgp_neighbors_detail, ipaddress.ip_address("192.0.2.250")
            )
        )
        self.assertIsNotNone(
            self.router.find_bgp_neighbor_detail(self.bgp_neighbors_detail, "192.0.2.1")
        )
        self.assertIsNotNone(
            self.router.find_bgp_neighbor_detail(
                self.bgp_neighbors_detail, ipaddress.ip_address("192.0.2.1")
            )
        )
        self.assertIsNone(
            self.router.find_bgp_neighbor_detail(
                self.bgp_neighbors_detail, "2001:db8::1337"
            )
        )
        self.assertIsNone(
            self.router.find_bgp_neighbor_detail(
                self.bgp_neighbors_detail, ipaddress.ip_address("2001:db8::1337")
            )
        )
        self.assertIsNotNone(
            self.router.find_bgp_neighbor_detail(
                self.bgp_neighbors_detail, "2001:db8::1"
            )
        )
        self.assertIsNotNone(
            self.router.find_bgp_neighbor_detail(
                self.bgp_neighbors_detail, ipaddress.ip_address("2001:db8::1")
            )
        )

    def test_set_napalm_configuration(self):
        error, changes = self.router.set_napalm_configuration(None)
        self.assertIsNotNone(error)
        self.assertIsNone(changes)
        error, changes = self.router.set_napalm_configuration({})
        self.assertIsNotNone(error)
        self.assertIsNone(changes)
        error, changes = self.router.set_napalm_configuration("")
        self.assertIsNotNone(error)
        self.assertIsNone(changes)


class RoutingPolicyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.routing_policies = [
            RoutingPolicy(name="test-1", slug="test-1", type=RoutingPolicyType.EXPORT),
            RoutingPolicy(name="test-2", slug="test-2", type=RoutingPolicyType.IMPORT),
            RoutingPolicy(
                name="test-3", slug="test-3", type=RoutingPolicyType.IMPORT_EXPORT
            ),
            RoutingPolicy(name="test-4", slug="test-4", type="unknown"),
        ]
        RoutingPolicy.objects.bulk_create(cls.routing_policies)

    def test_get_type_html(self):
        expected = [
            '<span class="badge badge-primary">Export</span>',
            '<span class="badge badge-info">Import</span>',
            '<span class="badge badge-dark">Import+Export</span>',
            '<span class="badge badge-secondary">Unknown</span>',
        ]

        for i in range(len(expected)):
            self.assertEqual(expected[i], self.routing_policies[i].get_type_html())
