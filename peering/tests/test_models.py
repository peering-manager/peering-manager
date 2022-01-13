import ipaddress
from unittest.mock import patch

from django.test import TestCase

from bgp.models import Relationship
from devices.models import PasswordAlgorithm, Platform
from net.models import Connection
from peering.enums import CommunityType, DeviceState, RoutingPolicyType
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from peering.tests.mocked_data import load_peeringdb_data, mocked_subprocess_popen
from utils.testing import load_json


class AutonomousSystemTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.autonomous_system = AutonomousSystem.objects.create(
            asn=65537, name="Test", irr_as_set="AS-MOCKED"
        )
        load_peeringdb_data()

    def test_create_from_peeringdb(self, *_):
        asn = 201281

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

    def test_synchronize_with_peeringdb(self, *_):
        # Create legal AS to sync with PeeringDB
        asn = 201281
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

    def test_peeringdb_network(self):
        self.assertIsNone(self.autonomous_system.peeringdb_network)

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
                name="test-1", slug="test-1", value="64500:1", type=CommunityType.EGRESS
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


class DirectPeeringSessionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.local_as = AutonomousSystem.objects.create(
            asn=64500, name="Local Test", affiliated=True
        )
        cls.autonomous_system = AutonomousSystem.objects.create(asn=64501, name="Test")
        cls.group = BGPGroup.objects.create(
            name="Test Group", slug="testgroup", check_bgp_session_states=True
        )
        cls.router = Router.objects.create(
            local_autonomous_system=cls.local_as,
            name="Test",
            hostname="test.example.com",
            platform=Platform.objects.get(name="Juniper Junos"),
        )
        cls.session = DirectPeeringSession.objects.create(
            local_autonomous_system=cls.local_as,
            autonomous_system=cls.autonomous_system,
            bgp_group=cls.group,
            relationship=Relationship.objects.create(name="Test", slug="test"),
            ip_address="2001:db8::1",
            password="mypassword",
            router=cls.router,
        )

    def test_poll(self):
        with patch(
            "peering.models.Router.get_bgp_neighbors_detail",
            return_value=self.router.find_bgp_neighbor_detail(
                load_json("peering/tests/fixtures/get_bgp_neighbors_detail.json"),
                "2001:db8::1",
            ),
        ):
            self.assertTrue(self.session.poll())
            self.assertEqual(567_257, self.session.received_prefix_count)


class InternetExchangeTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.autonomous_system = AutonomousSystem.objects.create(
            asn=65537, name="Test", irr_as_set="AS-MOCKED"
        )
        cls.internet_exchange = InternetExchange.objects.create(
            local_autonomous_system=cls.autonomous_system, name="Test", slug="test"
        )
        load_peeringdb_data()


class InternetExchangePeeringSessionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.local_as = AutonomousSystem.objects.create(
            asn=64500, name="Local Test", affiliated=True
        )
        cls.a_s = AutonomousSystem.objects.create(asn=64510, name="Test")
        cls.router = Router.objects.create(
            local_autonomous_system=cls.local_as,
            name="Test",
            hostname="test.example.com",
            platform=Platform.objects.get(name="Juniper Junos"),
        )
        cls.ixp = InternetExchange.objects.create(
            local_autonomous_system=cls.local_as,
            name="Test Group",
            slug="testgroup",
            check_bgp_session_states=True,
        )
        cls.ixp_connection = Connection.objects.create(
            vlan=2000, internet_exchange_point=cls.ixp, router=cls.router
        )
        cls.session = InternetExchangePeeringSession.objects.create(
            autonomous_system=cls.a_s,
            ixp_connection=cls.ixp_connection,
            ip_address="2001:db8::1",
            password="mypassword",
        )

    def test_encrypt_password(self):
        self.session.password = "mypassword"
        self.assertIsNotNone(self.session.password)
        self.assertIsNone(self.session.encrypted_password)

        # Try encrypting but without password algorithm for the platform
        self.session.encrypt_password()
        self.assertIsNone(self.session.encrypted_password)

        # Set password algorithm
        self.router.platform.password_algorithm = PasswordAlgorithm.JUNIPER_TYPE9
        self.router.platform.save()

        # Encrypt the password but router is not configured for it
        self.session.encrypt_password()
        self.assertIsNone(self.session.encrypted_password)

        # Enable password encryption for router
        self.router.encrypt_passwords = True
        self.router.save()

        # Encrypt the password
        self.session.encrypt_password()
        self.assertIsNotNone(self.session.encrypted_password)

        # Change router platform and re-encrypt
        self.router.platform = Platform.objects.get(name="Cisco IOS")
        self.router.save()
        old_encrypted_password = self.session.encrypted_password
        self.session.encrypt_password()
        self.assertNotEqual(old_encrypted_password, self.session.encrypted_password)

        # Change router platform to one without encryption support
        self.router.platform = Platform.objects.create(name="Huge OS", slug="huge-os")
        self.router.save()
        self.session.encrypt_password()
        self.assertNotEqual("", self.session.encrypted_password)

        # Change password to `None`
        self.session.password = None
        self.session.encrypt_password()
        self.assertIsNone(self.session.password)
        self.assertIsNone(self.session.encrypted_password)

    def test_exists_in_peeringdb(self):
        self.assertFalse(self.session.exists_in_peeringdb())

    def test_is_abandoned(self):
        self.assertFalse(self.session.is_abandoned())

    def test_poll(self):
        with patch(
            "peering.models.Router.get_bgp_neighbors_detail",
            return_value=self.router.find_bgp_neighbor_detail(
                load_json("peering/tests/fixtures/get_bgp_neighbors_detail.json"),
                "2001:db8::1",
            ),
        ):
            self.assertTrue(self.session.poll())
            self.assertEqual(567_257, self.session.received_prefix_count)


class RouterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.local_as = AutonomousSystem.objects.create(
            asn=64500, name="Autonomous System", affiliated=True
        )
        cls.bgp_neighbors_detail = load_json(
            "peering/tests/fixtures/get_bgp_neighbors_detail.json"
        )
        cls.router = Router.objects.create(
            local_autonomous_system=cls.local_as,
            name="Test",
            hostname="test.example.com",
            device_state=DeviceState.ENABLED,
        )

    def test_is_usable_for_task(self):
        self.assertFalse(self.router.is_usable_for_task())

    def test_get_configuration_context(self):
        # self.maxDiff = None
        for i in range(1, 6):
            AutonomousSystem.objects.create(asn=i, name=f"Test {i}")
        bgp_group = BGPGroup.objects.create(name="Test Group", slug="testgroup")
        relationship_private_peering = Relationship.objects.create(
            name="Private Peering", slug="private-peering"
        )
        for i in range(1, 6):
            DirectPeeringSession.objects.create(
                local_autonomous_system=self.local_as,
                local_ip_address="192.0.2.1",
                autonomous_system=AutonomousSystem.objects.get(asn=i),
                bgp_group=bgp_group,
                relationship=relationship_private_peering,
                ip_address=f"10.0.0.{i}",
                enabled=bool(i % 2),
                router=self.router,
            )
        ixp = InternetExchange.objects.create(
            local_autonomous_system=self.local_as, name="Test IX", slug="test-ix"
        )
        ixp_connection = Connection.objects.create(
            vlan=2000, internet_exchange_point=ixp, router=self.router
        )
        for i in range(1, 6):
            InternetExchangePeeringSession.objects.create(
                autonomous_system=AutonomousSystem.objects.get(asn=i),
                ixp_connection=ixp_connection,
                ip_address=f"2001:db8::{i}",
                enabled=bool(i % 2),
            )
            InternetExchangePeeringSession.objects.create(
                autonomous_system=AutonomousSystem.objects.get(asn=i),
                ixp_connection=ixp_connection,
                ip_address=f"192.0.2.{i}",
                enabled=bool(i % 2),
            )

        # Generate expected result
        expected = {
            "autonomous_systems": AutonomousSystem.objects.exclude(pk=self.local_as.pk),
            "bgp_groups": BGPGroup.objects.all(),
            "internet_exchange_points": InternetExchange.objects.all(),
            "local_as": self.local_as,
            "routing_policies": RoutingPolicy.objects.none(),
            "communities": Community.objects.none(),
            "router": self.router,
        }

        self.assertEqual(
            sorted(self.router.get_configuration_context()), sorted(expected)
        )

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
            device_state=DeviceState.ENABLED,
            local_autonomous_system=AutonomousSystem.objects.create(
                asn=64510, name="Autonomous System", affiliated=True
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
