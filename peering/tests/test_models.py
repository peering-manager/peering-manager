import ipaddress

from django.conf import settings
from django.test import TestCase
from unittest.mock import patch

from peering.constants import (
    BGP_RELATIONSHIP_PRIVATE_PEERING,
    COMMUNITY_TYPE_INGRESS,
    COMMUNITY_TYPE_EGRESS,
    PLATFORM_IOSXR,
    PLATFORM_JUNOS,
    PLATFORM_NONE,
    ROUTING_POLICY_TYPE_EXPORT,
    ROUTING_POLICY_TYPE_IMPORT,
    ROUTING_POLICY_TYPE_IMPORT_EXPORT,
)
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
    Template,
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
from utils.testing import MockedResponse


def mocked_peeringdb(*args, **kwargs):
    if "asn" in kwargs["params"] and kwargs["params"]["asn"] == 65536:
        return MockedResponse(fixture="peeringdb/tests/fixtures/as65536.json")

    return MockedResponse(status_code=404)


class AutonomousSystemTest(TestCase):
    def setUp(self):
        super().setUp()

        self.autonomous_system = AutonomousSystem.objects.create(
            asn=65537, name="Test", irr_as_set="AS-MOCKED"
        )

    def test_does_exist(self):
        asn = 201281

        # AS should not exist
        autonomous_system = AutonomousSystem.does_exist(asn)
        self.assertEqual(None, autonomous_system)

        # Create the AS
        new_as = AutonomousSystem.objects.create(asn=asn, name="Guillaume Mazoyer")

        # AS must exist
        autonomous_system = AutonomousSystem.does_exist(asn)
        self.assertEqual(asn, new_as.asn)

    @patch("peeringdb.http.requests.get", side_effect=mocked_peeringdb)
    def test_create_from_peeringdb(self, *_):
        asn = 65536

        # Illegal ASN
        self.assertIsNone(AutonomousSystem.create_from_peeringdb(64500))

        # Must not exist at first
        self.assertIsNone(AutonomousSystem.does_exist(asn))

        # Create the AS
        autonomous_system1 = AutonomousSystem.create_from_peeringdb(asn)
        self.assertEqual(asn, autonomous_system1.asn)

        # Must exist now
        self.assertEqual(asn, AutonomousSystem.does_exist(asn).asn)

        # Must not rise error, just return the AS
        autonomous_system2 = AutonomousSystem.create_from_peeringdb(asn)
        self.assertEqual(asn, autonomous_system2.asn)

        # Must exist now also
        self.assertEqual(asn, AutonomousSystem.does_exist(asn).asn)

    @patch("peeringdb.http.requests.get", side_effect=mocked_peeringdb)
    def test_synchronize_with_peeringdb(self, *_):
        # Create legal AS to sync with PeeringDB
        asn = 65536
        autonomous_system = AutonomousSystem.create_from_peeringdb(asn)
        self.assertEqual(asn, autonomous_system.asn)
        self.assertTrue(autonomous_system.synchronize_with_peeringdb())

        # Create illegal AS to fail sync with PeeringDB
        asn = 64500
        autonomous_system = AutonomousSystem.objects.create(asn=asn, name="Test")
        self.assertEqual(asn, autonomous_system.asn)
        self.assertFalse(autonomous_system.synchronize_with_peeringdb())

    def test_retrieve_irr_as_set_prefixes(self):
        with patch("peering.subprocess.Popen", side_effect=mocked_subprocess_popen):
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
        asn = 64500
        name = "Test"
        expected = "AS{} - {}".format(asn, name)
        autonomous_system = AutonomousSystem.objects.create(asn=asn, name=name)

        self.assertEqual(expected, str(autonomous_system))


class CommunityTest(TestCase):
    def test_create(self):
        community_list = [
            {"name": "Test", "value": "64500:1", "type": None, "str": "Test"},
            {
                "name": "Test",
                "value": "64500:1",
                "type": COMMUNITY_TYPE_EGRESS,
                "str": "Test",
            },
        ]

        for details in community_list:
            if details["type"]:
                community = Community.objects.create(
                    name=details["name"], value=details["value"], type=details["type"]
                )
            else:
                community = Community.objects.create(
                    name=details["name"], value=details["value"]
                )

            self.assertIsNotNone(community)
            self.assertEqual(details["name"], community.name)
            self.assertEqual(details["value"], community.value)
            self.assertEqual(details["type"] or COMMUNITY_TYPE_INGRESS, community.type)
            self.assertEqual(details["str"], str(community))

    def test_get_type_html(self):
        expected = [
            '<span class="badge badge-primary">Egress</span>',
            '<span class="badge badge-info">Ingress</span>',
            '<span class="badge badge-secondary">Unknown</span>',
        ]
        community_types = [COMMUNITY_TYPE_EGRESS, COMMUNITY_TYPE_INGRESS, "unknown"]

        for i in range(len(community_types)):
            self.assertEqual(
                expected[i],
                Community.objects.create(
                    name="test{}".format(i),
                    value="64500:{}".format(i),
                    type=community_types[i],
                ).get_type_html(),
            )


class DirectPeeringSessionTest(TestCase):
    def test_encrypt_password(self):
        autonomous_system = AutonomousSystem.objects.create(asn=64500, name="Test")
        router = Router.objects.create(
            name="Test", hostname="test.example.com", platform=PLATFORM_JUNOS
        )
        peering_session = DirectPeeringSession.objects.create(
            autonomous_system=autonomous_system,
            ip_address="2001:db8::1",
            password="mypassword",
            router=router,
        )
        self.assertIsNotNone(peering_session.password)
        self.assertIsNone(peering_session.encrypted_password)

        # Encrypt the password
        peering_session.encrypt_password(router.platform)
        self.assertIsNotNone(peering_session.encrypted_password)
        self.assertTrue(junos_is_encrypted(peering_session.encrypted_password))
        self.assertEqual(
            peering_session.password, junos_decrypt(peering_session.encrypted_password)
        )

        # Change router platform and re-encrypt
        router.platform = PLATFORM_IOSXR
        peering_session.encrypt_password(router.platform)
        self.assertIsNotNone(peering_session.encrypted_password)
        self.assertTrue(cisco_is_encrypted(peering_session.encrypted_password))
        self.assertEqual(
            peering_session.password, cisco_decrypt(peering_session.encrypted_password)
        )

        # Change router platform to an unsupported one
        router.platform = PLATFORM_NONE
        peering_session.encrypt_password(router.platform)
        self.assertIsNone(peering_session.encrypted_password)

        # Change password to None and
        peering_session.password = None
        router.platform = PLATFORM_JUNOS
        peering_session.encrypt_password(router.platform)
        self.assertIsNone(peering_session.encrypted_password)


class InternetExchangeTest(TestCase):
    def test_is_peeringdb_valid(self):
        ix = InternetExchange.objects.create(name="Test", slug="test")

        # Not linked with PeeringDB but considered as valid
        self.assertTrue(ix.is_peeringdb_valid())

        # Set invalid ID, must result in false
        ix.peeringdb_id = 14658
        ix.save()
        self.assertFalse(ix.is_peeringdb_valid())

        # Set valid ID, must result in true
        ix.peeringdb_id = 29146
        ix.save()
        self.assertTrue(ix.is_peeringdb_valid())

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
            [{"ip_address": ipaddress.ip_address("2001:db8::1"), "remote_asn": 29467}],
            # Second case, one new session with one known AS
            [{"ip_address": ipaddress.ip_address("192.0.2.1"), "remote_asn": 29467}],
            # Third case, new IPv4 session on another IX but with an IP that
            # has already been used
            [{"ip_address": ipaddress.ip_address("192.0.2.1"), "remote_asn": 29467}],
            # Fourth case, new IPv4 session with IPv6 prefix
            [{"ip_address": ipaddress.ip_address("203.0.113.1"), "remote_asn": 29467}],
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
    def test_does_exist(self):
        # No session, must expect None
        self.assertIsNone(InternetExchangePeeringSession.does_exist())

        # Prepare objects and create a peering session
        autonomous_system0 = AutonomousSystem.objects.create(asn=64500, name="Test")
        internet_exchange0 = InternetExchange.objects.create(name="Test0", slug="test0")
        peering_session0 = InternetExchangePeeringSession.objects.create(
            autonomous_system=autonomous_system0,
            internet_exchange=internet_exchange0,
            ip_address="2001:db8::1",
        )

        # Make sure that the session has been created
        self.assertIsNotNone(peering_session0)
        # Make sure that the session is returned by calling does_exist()
        # without arguments (only one session in the database)
        self.assertIsNotNone(InternetExchangePeeringSession.does_exist())
        # Make sure we can retrieve the session with its IP
        self.assertEqual(
            peering_session0,
            InternetExchangePeeringSession.does_exist(ip_address="2001:db8::1"),
        )
        # Make sure we can retrieve the session with its IX
        self.assertEqual(
            peering_session0,
            InternetExchangePeeringSession.does_exist(
                internet_exchange=internet_exchange0
            ),
        )
        # Make sure we can retrieve the session with AS
        self.assertEqual(
            peering_session0,
            InternetExchangePeeringSession.does_exist(
                autonomous_system=autonomous_system0
            ),
        )

        # Create another peering session
        peering_session1 = InternetExchangePeeringSession.objects.create(
            autonomous_system=autonomous_system0,
            internet_exchange=internet_exchange0,
            ip_address="198.51.100.1",
        )

        # Make sure that the session has been created
        self.assertIsNotNone(peering_session1)
        # More than one session, must expect None
        self.assertIsNone(InternetExchangePeeringSession.does_exist())
        # Make sure we can retrieve the session with its IP
        self.assertEqual(
            peering_session1,
            InternetExchangePeeringSession.does_exist(ip_address="198.51.100.1"),
        )
        # Make sure it returns None when using a field that the two sessions
        # have in common
        self.assertIsNone(
            InternetExchangePeeringSession.does_exist(
                internet_exchange=internet_exchange0
            )
        )

        # Create a new IX
        internet_exchange1 = InternetExchange.objects.create(name="Test1", slug="test1")

        # Make sure it returns None when there is no session
        self.assertIsNone(
            InternetExchangePeeringSession.does_exist(
                internet_exchange=internet_exchange1
            )
        )

        # Create a new session with a already used IP in another OX
        peering_session2 = InternetExchangePeeringSession.objects.create(
            autonomous_system=autonomous_system0,
            internet_exchange=internet_exchange1,
            ip_address="2001:db8::1",
        )

        # Make sure that the session has been created
        self.assertIsNotNone(peering_session2)
        # Make sure we have None, because two sessions will be found
        self.assertIsNone(
            InternetExchangePeeringSession.does_exist(ip_address="2001:db8::1")
        )
        # But if we narrow the search with the IX we must have the proper
        # session
        self.assertEqual(
            peering_session2,
            InternetExchangePeeringSession.does_exist(
                ip_address="2001:db8::1", internet_exchange=internet_exchange1
            ),
        )

    def test_encrypt_password(self):
        autonomous_system = AutonomousSystem.objects.create(asn=64500, name="Test")
        router = Router.objects.create(
            name="Test", hostname="test.example.com", platform=PLATFORM_JUNOS
        )
        internet_exchange = InternetExchange.objects.create(
            name="Test", slug="test", router=router
        )
        peering_session = InternetExchangePeeringSession.objects.create(
            autonomous_system=autonomous_system,
            internet_exchange=internet_exchange,
            ip_address="2001:db8::1",
            password="mypassword",
        )
        self.assertIsNotNone(peering_session.password)
        self.assertIsNone(peering_session.encrypted_password)

        # Encrypt the password
        peering_session.encrypt_password(router.platform)
        self.assertIsNotNone(peering_session.encrypted_password)
        self.assertTrue(junos_is_encrypted(peering_session.encrypted_password))
        self.assertEqual(
            peering_session.password, junos_decrypt(peering_session.encrypted_password)
        )

        # Change router platform and re-encrypt
        router.platform = PLATFORM_IOSXR
        peering_session.encrypt_password(router.platform)
        self.assertIsNotNone(peering_session.encrypted_password)
        self.assertTrue(cisco_is_encrypted(peering_session.encrypted_password))
        self.assertEqual(
            peering_session.password, cisco_decrypt(peering_session.encrypted_password)
        )

        # Change router platform to an unsupported one
        router.platform = PLATFORM_NONE
        peering_session.encrypt_password(router.platform)
        self.assertIsNone(peering_session.encrypted_password)

        # Change password to None and
        peering_session.password = None
        router.platform = PLATFORM_JUNOS
        peering_session.encrypt_password(router.platform)
        self.assertIsNone(peering_session.encrypted_password)

    def test_exists_in_peeringdb(self):
        autonomous_system = AutonomousSystem.objects.create(asn=64500, name="Test")
        internet_exchange = InternetExchange.objects.create(name="Test", slug="test")
        InternetExchangePeeringSession.objects.create(
            autonomous_system=autonomous_system,
            internet_exchange=internet_exchange,
            ip_address="2001:db8::1",
        )
        self.assertFalse(
            InternetExchangePeeringSession.objects.get(
                ip_address="2001:db8::1"
            ).exists_in_peeringdb()
        )

    def test_is_abandoned(self):
        autonomous_system = AutonomousSystem.objects.create(asn=64500, name="Test")
        internet_exchange = InternetExchange.objects.create(name="Test", slug="test")
        peering_session = InternetExchangePeeringSession.objects.create(
            autonomous_system=autonomous_system,
            internet_exchange=internet_exchange,
            ip_address="2001:db8::1",
        )
        self.assertFalse(peering_session.is_abandoned())


class RouterTest(TestCase):
    def setUp(self):
        super().setUp()
        self.router = Router.objects.create(
            name="Test", hostname="test.example.com", platform=PLATFORM_JUNOS
        )

    def test_get_configuration_context(self):
        for i in range(1, 6):
            AutonomousSystem.objects.create(asn=i, name="Test {}".format(i))
        bgp_group = BGPGroup.objects.create(name="Test Group", slug="testgroup")
        for i in range(1, 6):
            DirectPeeringSession.objects.create(
                local_ip_address="192.0.2.1",
                autonomous_system=AutonomousSystem.objects.get(asn=i),
                bgp_group=bgp_group,
                relationship=BGP_RELATIONSHIP_PRIVATE_PEERING,
                ip_address="10.0.0.{}".format(i),
                router=self.router,
            )
        internet_exchange = InternetExchange.objects.create(
            name="Test IX", slug="testix", router=self.router
        )
        for i in range(1, 6):
            InternetExchangePeeringSession.objects.create(
                autonomous_system=AutonomousSystem.objects.get(asn=i),
                internet_exchange=internet_exchange,
                ip_address="2001:db8::{}".format(i),
            )
            InternetExchangePeeringSession.objects.create(
                autonomous_system=AutonomousSystem.objects.get(asn=i),
                internet_exchange=internet_exchange,
                ip_address="192.0.2.{}".format(i),
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
            "autonomous_systems": [
                autonomous_system.to_dict()
                for autonomous_system in AutonomousSystem.objects.all()
            ],
            "my_asn": settings.MY_ASN,
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
            name="test", hostname="test.example.com", platform=PLATFORM_JUNOS
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
                "up": True,
                "local_as": 201281,
                "remote_as": 29467,
                "local_address": "198.51.100.1",
            }
        ]
        bgp_neighbors_detail = {
            "global": {
                29467: [
                    {
                        "up": True,
                        "local_as": 201281,
                        "remote_as": 29467,
                        "local_address": "198.51.100.1",
                    }
                ]
            }
        }

        router = Router.objects.create(
            name="test", hostname="test.example.com", platform=PLATFORM_JUNOS
        )
        self.assertEqual(
            expected, router.bgp_neighbors_detail_as_list(bgp_neighbors_detail)
        )


class RoutingPolicyTest(TestCase):
    def test_create(self):
        routing_policy_list = [
            {"name": "Test1", "slug": "test1", "type": None, "weight": 0},
            {
                "name": "Test2",
                "slug": "test2",
                "type": ROUTING_POLICY_TYPE_EXPORT,
                "weight": 0,
            },
        ]

        for details in routing_policy_list:
            if details["type"]:
                routing_policy = RoutingPolicy.objects.create(
                    name=details["name"], slug=details["slug"], type=details["type"]
                )
            else:
                routing_policy = RoutingPolicy.objects.create(
                    name=details["name"], slug=details["slug"]
                )

            self.assertIsNotNone(routing_policy)
            self.assertEqual(details["name"], routing_policy.name)
            self.assertEqual(details["slug"], routing_policy.slug)
            self.assertEqual(
                details["type"] or ROUTING_POLICY_TYPE_IMPORT, routing_policy.type
            )

    def test_get_type_html(self):
        expected = [
            '<span class="badge badge-primary">Export</span>',
            '<span class="badge badge-info">Import</span>',
            '<span class="badge badge-dark">Import+Export</span>',
            '<span class="badge badge-secondary">Unknown</span>',
        ]
        routing_policy_types = [
            ROUTING_POLICY_TYPE_EXPORT,
            ROUTING_POLICY_TYPE_IMPORT,
            ROUTING_POLICY_TYPE_IMPORT_EXPORT,
            "unknown",
        ]

        for i in range(len(routing_policy_types)):
            self.assertEqual(
                expected[i],
                RoutingPolicy.objects.create(
                    name="test{}".format(i),
                    slug="test{}".format(i),
                    type=routing_policy_types[i],
                ).get_type_html(),
            )


class TemplateTest(TestCase):
    def setUp(self):
        super().setUp()
        self.template = Template(name="Test", template="{{ test }}")

    def test_render(self):
        self.assertEqual(self.template.render({"test": "test"}), "test")
