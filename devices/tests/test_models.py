import ipaddress
from unittest.mock import patch

from django.test import TestCase

from bgp.models import Community, Relationship
from net.models import Connection
from peering.enums import BGPSessionStatus
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)
from utils.testing import load_json

from ..enums import *
from ..models import *


class ConfigurationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.template = Configuration.objects.create(name="Test", template="{{ test }}")

    def test_render(self):
        self.assertEqual(self.template.render({"test": "test"}), "test")
        self.template.template = "{% for i in range(5) %}\n{{ i }}\n{% endfor %}"
        self.assertEqual(self.template.render({}), "\n0\n\n1\n\n2\n\n3\n\n4\n")
        self.template.jinja2_trim = True
        self.assertEqual(self.template.render({}), "0\n1\n2\n3\n4\n")


class PlatformTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.platforms = [
            Platform(
                name="Mercuros",
                slug="mercuros",
                password_algorithm=PasswordAlgorithm.JUNIPER_TYPE9,
            ),
            Platform(
                name="Test OS",
                slug="test-os",
                password_algorithm=PasswordAlgorithm.CISCO_TYPE7,
            ),
            Platform(name="Wrong OS", slug="wrong-os"),
        ]
        Platform.objects.bulk_create(cls.platforms)

    def test_password_encryption_decryption(self):
        clear_text_password = "mypassword"
        junos = Platform.objects.filter(
            password_algorithm=PasswordAlgorithm.JUNIPER_TYPE9
        ).first()
        encrypted_password = junos.encrypt_password(clear_text_password)
        self.assertNotEqual(clear_text_password, encrypted_password)
        self.assertEqual(
            clear_text_password, junos.decrypt_password(encrypted_password)
        )

        cisco = Platform.objects.filter(
            password_algorithm=PasswordAlgorithm.CISCO_TYPE7
        ).first()
        encrypted_password = cisco.encrypt_password(clear_text_password)
        self.assertNotEqual(clear_text_password, encrypted_password)
        self.assertEqual(
            clear_text_password, cisco.decrypt_password(encrypted_password)
        )

        wrong = Platform.objects.filter(password_algorithm="").first()
        encrypted_password = wrong.encrypt_password(clear_text_password)
        self.assertEqual(clear_text_password, encrypted_password)
        self.assertEqual(
            clear_text_password, wrong.decrypt_password(encrypted_password)
        )


class RouterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.local_as = AutonomousSystem.objects.create(
            asn=64500, name="Autonomous System", affiliated=True
        )
        cls.bgp_neighbors_detail = load_json(
            "devices/tests/fixtures/get_bgp_neighbors_detail.json"
        )
        cls.router = Router.objects.create(
            local_autonomous_system=cls.local_as,
            name="Test",
            hostname="test.example.com",
            status=DeviceStatus.ENABLED,
            poll_bgp_sessions_state=True,
        )

    def test_is_usable_for_task(self):
        self.assertFalse(self.router.is_usable_for_task())

    def test_get_configuration_context(self):
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
                status=(
                    BGPSessionStatus.ENABLED
                    if bool(i % 2)
                    else BGPSessionStatus.DISABLED
                ),
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
                status=(
                    BGPSessionStatus.ENABLED
                    if bool(i % 2)
                    else BGPSessionStatus.DISABLED
                ),
            )
            InternetExchangePeeringSession.objects.create(
                autonomous_system=AutonomousSystem.objects.get(asn=i),
                ixp_connection=ixp_connection,
                ip_address=f"192.0.2.{i}",
                status=(
                    BGPSessionStatus.ENABLED
                    if bool(i % 2)
                    else BGPSessionStatus.DISABLED
                ),
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
            status=DeviceStatus.ENABLED,
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

    def test_poll_bgp_sessions(self):
        with patch(
            "devices.models.Router.get_bgp_neighbors_detail",
            return_value=load_json(
                "devices/tests/fixtures/get_bgp_neighbors_detail.json"
            ),
        ):
            self.assertTupleEqual((False, 0), self.router.poll_bgp_sessions())

            autonomous_system = AutonomousSystem.objects.create(
                asn=64666, name="Poll Testing"
            )
            group = BGPGroup.objects.create(name="Poll Testing", slug="poll-testing")
            relationship = Relationship.objects.create(
                name="Poll Testing", slug="poll-testing"
            )
            self.router.platform = Platform.objects.get(slug="juniper-junos")
            self.router.save()
            session = DirectPeeringSession.objects.create(
                local_autonomous_system=self.local_as,
                local_ip_address="2001:db8::2/126",
                autonomous_system=autonomous_system,
                bgp_group=group,
                relationship=relationship,
                ip_address="2001:db8::1/126",
                status=BGPSessionStatus.ENABLED,
                router=self.router,
            )

            self.assertTupleEqual((True, 1), self.router.poll_bgp_sessions())
            session.refresh_from_db()
            self.assertEqual(567_257, session.received_prefix_count)

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
