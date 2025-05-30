from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from bgp.models import Relationship
from devices.models import PasswordAlgorithm, Platform, Router
from net.models import Connection
from peering.fields import validate_bgp_community
from utils.testing import load_json

from ..enums import CommunityType, RoutingPolicyType
from ..models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)
from .mocked_data import load_peeringdb_data, mocked_subprocess_popen


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

    def test_synchronise_with_peeringdb(self, *_):
        # Create legal AS to sync with PeeringDB
        asn = 201281
        a_s = AutonomousSystem.create_from_peeringdb(asn)
        self.assertEqual(asn, a_s.asn)
        self.assertTrue(a_s.synchronise_with_peeringdb())

        # Private AS passes sync even if not synced for real
        asn = 64500
        a_s = AutonomousSystem.objects.create(asn=asn, name="Test")
        self.assertEqual(asn, a_s.asn)
        self.assertTrue(a_s.synchronise_with_peeringdb())

        # Private AS passes sync even if not synced for real
        asn = 1
        a_s = AutonomousSystem.objects.create(asn=asn, name="Not in PeeringDB")
        self.assertEqual(asn, a_s.asn)
        self.assertFalse(a_s.synchronise_with_peeringdb())

    def test_retrieve_irr_as_set_prefixes(self):
        with patch(
            "peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen
        ):
            prefixes = self.autonomous_system.retrieve_irr_as_set_prefixes()
            self.assertEqual(1, len(prefixes["ipv6"]))
            self.assertEqual(1, len(prefixes["ipv4"]))

        with patch(
            "peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen
        ):
            self.autonomous_system.irr_as_set = "AS-ERROR"
            prefixes = self.autonomous_system.retrieve_irr_as_set_prefixes()
            self.assertEqual(1, len(prefixes["ipv6"]))
            self.assertEqual(1, len(prefixes["ipv4"]))

    def test_get_irr_as_set_prefixes(self):
        with patch(
            "peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen
        ):
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
            '<span class="badge text-bg-primary">Egress</span>',
            '<span class="badge text-bg-info">Ingress</span>',
            '<span class="badge text-bg-secondary">Not set</span>',
        ]

        for i in range(len(expected)):
            self.assertEqual(expected[i], self.communities[i].get_type_html())

    def test_community_validator(self):
        valid = [
            "65000:400",
            "100:200",
            "1:1",
            "target:65000:100",
            "origin:65000:200",
            "target:192.168.0.1:500",
            "65000:100:200",
            "1:0:0",
            "4294967295:4294967295:4294967295",
        ]
        for community in valid:
            try:
                validate_bgp_community(community)
            except ValidationError:
                self.fail(
                    f"validate_bgp_community raised ValidationError unexpectedly for {community}"
                )

        invalid = [
            "65000",
            "65536:100",
            "65000:65536",
            "65000:abc",
            "65000:-1",
            "target:65000:5000000000",
            "target::500",
            "target:192.168.0.1:-1",
            "65000:100:100:100",
            "65000:4294967296:0",
            "4294967296:100:100",
            "65000:100:abc",
            "65000:-1:100",
        ]
        for community in invalid:
            with self.assertRaises(
                ValidationError, msg=f"{community} should be invalid"
            ):
                validate_bgp_community(community)


class DirectPeeringSessionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.local_as = AutonomousSystem.objects.create(
            asn=64500, name="Local Test", affiliated=True
        )
        cls.autonomous_system = AutonomousSystem.objects.create(asn=64501, name="Test")
        cls.group = BGPGroup.objects.create(name="Test Group", slug="testgroup")
        cls.router = Router.objects.create(
            local_autonomous_system=cls.local_as,
            name="Test",
            hostname="test.example.com",
            platform=Platform.objects.get(name="Juniper Junos"),
            poll_bgp_sessions_state=True,
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
            "devices.models.Router.get_bgp_neighbors_detail",
            return_value=self.router.find_bgp_neighbor_detail(
                load_json("devices/tests/fixtures/get_bgp_neighbors_detail.json"),
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
            poll_bgp_sessions_state=True,
        )
        cls.ixp = InternetExchange.objects.create(
            local_autonomous_system=cls.local_as, name="Test Group", slug="testgroup"
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
        self.assertFalse(self.session.exists_in_peeringdb)

    def test_is_abandoned(self):
        self.assertFalse(self.session.is_abandoned)

    def test_poll(self):
        with patch(
            "devices.models.Router.get_bgp_neighbors_detail",
            return_value=self.router.find_bgp_neighbor_detail(
                load_json("devices/tests/fixtures/get_bgp_neighbors_detail.json"),
                "2001:db8::1",
            ),
        ):
            self.assertTrue(self.session.poll())
            self.assertEqual(567_257, self.session.received_prefix_count)


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
