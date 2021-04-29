from django.test import TestCase

from net.models import Connection
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)
from peering.models.jinja2 import FILTER_DICT
from utils.models import Tag


class Jinja2FilterTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tags = [
            Tag(name="Tag 1", slug="tag-1"),
            Tag(name="Tag 2", slug="tag-2"),
            Tag(name="Tag 3", slug="tag-3"),
        ]
        Tag.objects.bulk_create(cls.tags)
        cls.routing_policies = [
            RoutingPolicy(name="Reject All", slug="reject-all", weight=255),
            RoutingPolicy(name="Accept All", slug="accept-all", weight=255),
            RoutingPolicy(
                name="Import Known Prefixes", slug="import-known-prefixes", weight=128
            ),
            RoutingPolicy(name="Export Supernets", slug="export-supernets", weight=64),
            RoutingPolicy(name="Export Deaggregated", slug="export-deaggregated"),
        ]
        RoutingPolicy.objects.bulk_create(cls.routing_policies)
        AutonomousSystem.objects.create(asn=64520, name="Useless")
        cls.a_s = AutonomousSystem.objects.create(
            asn=64510, name="Test", ipv6_max_prefixes=100
        )
        cls.a_s.import_routing_policies.add(
            RoutingPolicy.objects.get(slug="import-known-prefixes")
        )
        cls.a_s.export_routing_policies.add(
            RoutingPolicy.objects.get(slug="export-supernets")
        )
        cls.a_s.tags.add(*cls.tags)
        cls.ixp = InternetExchange.objects.create(
            local_autonomous_system=AutonomousSystem.objects.create(
                asn=64500,
                name="Autonomous System",
                affiliated=True,
            ),
            name="Test IXP",
            slug="test-ixp",
        )
        cls.ixp.import_routing_policies.add(
            RoutingPolicy.objects.get(slug="reject-all")
        )
        cls.ixp.export_routing_policies.add(
            RoutingPolicy.objects.get(slug="reject-all")
        )
        cls.ixp_connection = Connection.objects.create(
            vlan=10,
            internet_exchange_point=cls.ixp,
            ipv4_address="192.0.2.10",
            ipv6_address="2001:db8::a",
        )
        cls.session6 = InternetExchangePeeringSession.objects.create(
            autonomous_system=cls.a_s,
            ixp_connection=cls.ixp_connection,
            ip_address="2001:db8::1",
            password="mypassword",
        )
        cls.session4 = InternetExchangePeeringSession.objects.create(
            autonomous_system=cls.a_s,
            ixp_connection=cls.ixp_connection,
            ip_address="192.0.2.1",
            password="mypassword",
        )
        cls.rs_session6 = InternetExchangePeeringSession.objects.create(
            autonomous_system=cls.a_s,
            ixp_connection=cls.ixp_connection,
            ip_address="2001:db8::ffff",
            is_route_server=True,
        )
        cls.rs_session4 = InternetExchangePeeringSession.objects.create(
            autonomous_system=cls.a_s,
            ixp_connection=cls.ixp_connection,
            ip_address="192.0.2.255",
            is_route_server=True,
        )
        cls.session6.import_routing_policies.add(
            RoutingPolicy.objects.get(slug="accept-all")
        )
        cls.session6.export_routing_policies.add(
            RoutingPolicy.objects.get(slug="accept-all"),
            RoutingPolicy.objects.get(slug="export-supernets"),
        )

    def test_ipv4(self):
        self.assertTrue(FILTER_DICT["ipv4"](self.session4.ip_address))
        self.assertFalse(FILTER_DICT["ipv4"](self.session6.ip_address))
        self.assertFalse(FILTER_DICT["ipv4"]("notanip"))

    def test_ipv6(self):
        self.assertTrue(FILTER_DICT["ipv6"](self.session6.ip_address))
        self.assertFalse(FILTER_DICT["ipv6"](self.session4.ip_address))
        self.assertFalse(FILTER_DICT["ipv6"]("notanip"))

    def test_ip_version(self):
        self.assertEquals(6, FILTER_DICT["ip_version"](self.session6))
        self.assertEquals(4, FILTER_DICT["ip_version"](self.session4))

    def test_max_prefix(self):
        self.assertEquals(100, FILTER_DICT["max_prefix"](self.session6))
        self.assertEquals(0, FILTER_DICT["max_prefix"](self.session4))

    def test_cisco_password(self):
        pass

    def test_filter(self):
        sessions = InternetExchangePeeringSession.objects.all()
        filtered = FILTER_DICT["filter"](sessions, ip_address__family=6)
        self.assertEquals(4, FILTER_DICT["length"](sessions))
        self.assertEquals(2, FILTER_DICT["length"](filtered))

    def test_iterate(self):
        routing_policies = RoutingPolicy.objects.all()
        slugs = [s for s in FILTER_DICT["iterate"](routing_policies, "slug")]
        self.assertListEqual([rp.slug for rp in routing_policies], slugs)

    def test_length(self):
        self.assertEquals(5, FILTER_DICT["length"](RoutingPolicy.objects.all()))
        self.assertEquals(0, FILTER_DICT["length"](RoutingPolicy.objects.none()))

    def test_cisco_password(self):
        pass

    def test_iter_export_policies(self):
        self.assertListEqual(
            [
                RoutingPolicy.objects.get(slug="accept-all"),
                RoutingPolicy.objects.get(slug="export-supernets"),
            ],
            FILTER_DICT["iter_export_policies"](self.session6),
        )

    def test_iter_import_policies(self):
        self.assertListEqual(
            [RoutingPolicy.objects.get(slug="accept-all")],
            FILTER_DICT["iter_import_policies"](self.session6),
        )

    def test_merge_export_policies(self):
        self.assertListEqual(
            [
                RoutingPolicy.objects.get(slug="accept-all"),
                RoutingPolicy.objects.get(slug="export-supernets"),
                RoutingPolicy.objects.get(slug="reject-all"),
            ],
            FILTER_DICT["merge_export_policies"](self.session6),
        )

    def test_merge_import_policies(self):
        self.assertListEqual(
            [
                RoutingPolicy.objects.get(slug="accept-all"),
                RoutingPolicy.objects.get(slug="import-known-prefixes"),
                RoutingPolicy.objects.get(slug="reject-all"),
            ],
            FILTER_DICT["merge_import_policies"](self.session6),
        )

    def test_sessions(self):
        self.assertEquals(4, FILTER_DICT["sessions"](self.ixp).count())
        self.assertEquals(2, FILTER_DICT["sessions"](self.ixp, family=6).count())
        self.assertEquals(2, FILTER_DICT["sessions"](self.ixp, family=4).count())

    def test_route_server(self):
        self.assertEquals(2, FILTER_DICT["route_server"](self.ixp).count())

    def direct_peers(self):
        self.assertEquals(0, FILTER_DICT["direct_peers"](self.router).count())

    def ixp_peers(self):
        self.assertEquals(1, FILTER_DICT["ixp_peers"](self.router).count())
        self.assertEquals(1, FILTER_DICT["ixp_peers"](self.router, "test-ixp").count())

    def test_prefix_list(self):
        pass

    def test_tags(self):
        self.assertEquals(3, FILTER_DICT["tags"](self.a_s).count())
        self.assertEquals(0, FILTER_DICT["tags"](self.ixp).count())
