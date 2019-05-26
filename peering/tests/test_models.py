import ipaddress

from django.conf import settings
from django.test import TestCase

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
    ConfigurationTemplate,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)


class AutonomousSystemTest(TestCase):
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

    def test_create_from_peeringdb(self):
        asn = 201281

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

    def test_synchronize_with_peeringdb(self):
        # Create legal AS to sync with PeeringDB
        asn = 201281
        autonomous_system = AutonomousSystem.create_from_peeringdb(asn)
        self.assertEqual(asn, autonomous_system.asn)
        self.assertTrue(autonomous_system.synchronize_with_peeringdb())

        # Create illegal AS to fail sync with PeeringDB
        asn = 64500
        autonomous_system = AutonomousSystem.objects.create(asn=asn, name="Test")
        self.assertEqual(asn, autonomous_system.asn)
        self.assertFalse(autonomous_system.synchronize_with_peeringdb())

    def test_get_irr_as_set_prefixes(self):
        autonomous_system = AutonomousSystem.create_from_peeringdb(201281)
        prefixes = autonomous_system.get_irr_as_set_prefixes()
        self.assertEqual(autonomous_system.ipv6_max_prefixes, len(prefixes["ipv6"]))
        self.assertEqual(autonomous_system.ipv4_max_prefixes, len(prefixes["ipv4"]))

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


class ConfigurationTemplateTest(TestCase):
    def setUp(self):
        super().setUp()
        self.configuration_template = ConfigurationTemplate(
            name="Test", template="{{ test }}"
        )

    def test_render(self):
        self.assertEqual(self.configuration_template.render({"test": "test"}), "test")


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
            {"ipv4_address": "192.168.168.1"},
            {"ipv6_address": "2001:db8::1", "ipv4_address": "192.168.168.1"},
            {"ipv6_address": "2001:7f8:1::a502:9467:1"},
            {"ipv4_address": "80.249.212.207"},
            {
                "ipv6_address": "2001:7f8:1::a502:9467:1",
                "ipv4_address": "80.249.212.207",
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
            [{"ip_address": ipaddress.ip_address("192.168.0.1"), "remote_asn": 29467}],
            # Third case, new IPv4 session on another IX but with an IP that
            # has already been used
            [{"ip_address": ipaddress.ip_address("192.168.0.1"), "remote_asn": 29467}],
            # Fourth case, new IPv4 session with IPv6 prefix
            [{"ip_address": ipaddress.ip_address("192.168.2.1"), "remote_asn": 29467}],
        ]

        prefix_lists = [
            # First case
            [ipaddress.ip_network("2001:db8::/64")],
            # Second case
            [ipaddress.ip_network("192.168.0.0/24")],
            # Third case
            [ipaddress.ip_network("192.168.0.0/24")],
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

    def test_generate_configuration(self):
        # Test setup
        internet_exchange = InternetExchange.objects.create(name="Test", slug="test")
        for i in range(1, 6):
            InternetExchangePeeringSession.objects.create(
                autonomous_system=AutonomousSystem.objects.create(
                    asn=i, name="Test {}".format(i)
                ),
                internet_exchange=internet_exchange,
                ip_address="2001:db8::{}".format(i),
            )

        # Generate expected result
        expected = [
            {
                "ip_version": 6,
                "peers": {
                    1: AutonomousSystem.objects.get(asn=1).to_dict(),
                    2: AutonomousSystem.objects.get(asn=2).to_dict(),
                    3: AutonomousSystem.objects.get(asn=3).to_dict(),
                    4: AutonomousSystem.objects.get(asn=4).to_dict(),
                    5: AutonomousSystem.objects.get(asn=5).to_dict(),
                },
            },
            {"ip_version": 4, "peers": {}},
        ]
        for i in range(1, 6):
            expected[0]["peers"][i].update(
                {
                    "sessions": [
                        InternetExchangePeeringSession.objects.get(
                            ip_address="2001:db8::{}".format(i)
                        ).to_dict()
                    ]
                }
            )

        result = internet_exchange._get_configuration_variables()
        self.assertEqual(result["peering_groups"], expected)


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
            ip_address="192.168.1.1",
        )

        # Make sure that the session has been created
        self.assertIsNotNone(peering_session1)
        # More than one session, must expect None
        self.assertIsNone(InternetExchangePeeringSession.does_exist())
        # Make sure we can retrieve the session with its IP
        self.assertEqual(
            peering_session1,
            InternetExchangePeeringSession.does_exist(ip_address="192.168.1.1"),
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


class RouterTest(TestCase):
    def setUp(self):
        super().setUp()
        self.router = Router.objects.create(
            name="Test", hostname="test.example.com", platform=PLATFORM_JUNOS
        )

    def test_generate_configuration(self):
        for i in range(1, 6):
            AutonomousSystem.objects.create(asn=i, name="Test {}".format(i))
        bgp_group = BGPGroup.objects.create(name="Test Group", slug="testgroup")
        for i in range(1, 6):
            DirectPeeringSession.objects.create(
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
                ip_address="192.168.0.{}".format(i),
            )

        # Generate expected result
        expected = {
            "my_asn": settings.MY_ASN,
            "bgp_groups": [
                {
                    "bgp_group": bgp_group.to_dict(),
                    "ipv6_sessions": [
                        session.to_dict()
                        for session in DirectPeeringSession.objects.filter(
                            ip_address__family=6
                        )
                    ],
                    "ipv4_sessions": [
                        session.to_dict()
                        for session in DirectPeeringSession.objects.filter(
                            ip_address__family=4
                        )
                    ],
                }
            ],
            "internet_exchanges": [
                {
                    "internet_exchange": internet_exchange.to_dict(),
                    "ipv6_sessions": [
                        session.to_dict()
                        for session in InternetExchangePeeringSession.objects.filter(
                            ip_address__family=6
                        )
                    ],
                    "ipv4_sessions": [
                        session.to_dict()
                        for session in InternetExchangePeeringSession.objects.filter(
                            ip_address__family=4
                        )
                    ],
                }
            ],
        }

        result = self.router.get_configuration_context()
        self.assertEqual(result, expected)

    def test_decrypt_encrypt_string(self):
        string = "myreallysecurepassword"

        # Generic router (crypto not implemented)
        router = Router.objects.create(
            name="test", hostname="test.example.com", platform=PLATFORM_NONE
        )
        self.assertEqual(string, router.decrypt_string(router.encrypt_string(string)))

        for platform in [PLATFORM_JUNOS, PLATFORM_IOSXR]:
            router = Router.objects.create(
                name="test", hostname="test.example.com", platform=platform
            )
            self.assertEqual(
                string, router.decrypt_string(router.encrypt_string(string))
            )

            # Should detect that it is already encrypted
            self.assertEqual(
                string,
                router.decrypt_string(
                    router.encrypt_string(router.encrypt_string(string))
                ),
            )
            # Should detect that it is not encrypted
            self.assertEqual(
                string, router.decrypt_string(router.decrypt_string(string))
            )

    def test_napalm_bgp_neighbors_to_peer_list(self):
        # Expected results
        expected = [0, 0, 1, 2, 3, 2, 2]

        napalm_dicts_list = [
            # If None or empty dict passed, returned value must be empty list
            None,
            {},
            # List size must match peers number including VRFs
            {"global": {"peers": {"192.168.0.1": {"remote_as": 64500}}}},
            {
                "global": {"peers": {"192.168.0.1": {"remote_as": 64500}}},
                "vrf": {"peers": {"192.168.1.1": {"remote_as": 64501}}},
            },
            {
                "global": {"peers": {"192.168.0.1": {"remote_as": 64500}}},
                "vrf0": {"peers": {"192.168.1.1": {"remote_as": 64501}}},
                "vrf1": {"peers": {"192.168.2.1": {"remote_as": 64502}}},
            },
            # If peer does not have remote_as field, it must be ignored
            {
                "global": {"peers": {"192.168.0.1": {"remote_as": 64500}}},
                "vrf0": {"peers": {"192.168.1.1": {"remote_as": 64501}}},
                "vrf1": {"peers": {"192.168.2.1": {"not_valid": 64502}}},
            },
            # If an IP address appears more than one time, only the first
            # occurence  must be retained
            {
                "global": {"peers": {"192.168.0.1": {"remote_as": 64500}}},
                "vrf0": {"peers": {"192.168.1.1": {"remote_as": 64501}}},
                "vrf1": {"peers": {"192.168.1.1": {"remote_as": 64502}}},
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
                "local_address": "192.168.1.1",
            }
        ]
        bgp_neighbors_detail = {
            "global": {
                8121: [
                    {
                        "up": True,
                        "local_as": 201281,
                        "remote_as": 29467,
                        "local_address": "192.168.1.1",
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
