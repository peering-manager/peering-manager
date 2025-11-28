import ipaddress
import json

import yaml
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from bgp.enums import CommunityType
from bgp.models import Community
from devices.enums import DeviceStatus
from devices.models import Configuration, Router
from extras.models import ExportTemplate, Tag
from messaging.models import Contact, ContactAssignment, ContactRole, Email
from net.enums import ConnectionStatus
from net.models import Connection
from peering.enums import BGPGroupStatus, BGPSessionStatus, IPFamily
from peering.models import (
    AutonomousSystem,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)
from peering_manager.jinja2 import FILTER_DICT


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
            RoutingPolicy(
                name="Export Deaggregated v4",
                slug="export-deaggregated-v4",
                address_family=IPFamily.IPV4,
            ),
            RoutingPolicy(
                name="Export Deaggregated v6",
                slug="export-deaggregated-v6",
                address_family=IPFamily.IPV6,
            ),
        ]
        RoutingPolicy.objects.bulk_create(cls.routing_policies)
        cls.communities = [
            Community(name="Learnt from IXP", slug="learnt-from-ixp", value="123:1"),
            Community(
                name="Learnt from direct peer",
                slug="learnt-from-direct-peer",
                value="123:2",
            ),
            Community(
                name="Learnt from transit",
                slug="learnt-from-transit",
                value="123:3",
                type=CommunityType.INGRESS,
            ),
        ]
        Community.objects.bulk_create(cls.communities)
        AutonomousSystem.objects.create(asn=64520, name="Useless")
        cls.a_s = AutonomousSystem.objects.create(
            asn=64510, name="Test", ipv6_max_prefixes=100
        )
        cls.a_s.import_routing_policies.add(
            RoutingPolicy.objects.get(slug="import-known-prefixes")
        )
        cls.a_s.export_routing_policies.add(
            RoutingPolicy.objects.get(slug="export-supernets"),
            RoutingPolicy.objects.get(slug="export-deaggregated-v4"),
            RoutingPolicy.objects.get(slug="export-deaggregated-v6"),
        )
        cls.a_s.communities.add(Community.objects.get(slug="learnt-from-transit"))
        cls.a_s.tags.add(*cls.tags)
        cls.router = Router.objects.create(
            name="test",
            hostname="test.example.com",
            local_context_data={"foo": "bar", "nested": {"inside": True}},
        )
        cls.ixp = InternetExchange.objects.create(
            local_autonomous_system=AutonomousSystem.objects.create(
                asn=64500, name="Autonomous System", affiliated=True
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
        cls.ixp.communities.add(Community.objects.get(slug="learnt-from-ixp"))
        cls.ixp_connection = Connection.objects.create(
            vlan=10,
            internet_exchange_point=cls.ixp,
            mac_address="00:1b:77:49:54:fd",
            ipv4_address="192.0.2.10",
            ipv6_address="2001:db8::a",
            router=cls.router,
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
        cls.contact = Contact.objects.create(name="Contact 1")
        cls.contact_role = ContactRole.objects.create(
            name="Contact Role 1", slug="contact-role-1"
        )
        ContactAssignment.objects.create(
            object=cls.a_s, contact=cls.contact, role=cls.contact_role
        )

    def test_ipv4(self):
        self.assertTrue(FILTER_DICT["ipv4"](self.session4.ip_address))
        self.assertTrue(FILTER_DICT["ipv4"](self.ixp_connection.ipv4_address))
        self.assertFalse(FILTER_DICT["ipv4"](self.session6.ip_address))
        self.assertFalse(FILTER_DICT["ipv4"](self.ixp_connection.ipv6_address))
        self.assertFalse(FILTER_DICT["ipv4"]("notanip"))

    def test_ipv6(self):
        self.assertTrue(FILTER_DICT["ipv6"](self.session6.ip_address))
        self.assertTrue(FILTER_DICT["ipv6"](self.ixp_connection.ipv6_address))
        self.assertFalse(FILTER_DICT["ipv6"](self.session4.ip_address))
        self.assertFalse(FILTER_DICT["ipv6"](self.ixp_connection.ipv4_address))
        self.assertFalse(FILTER_DICT["ipv6"]("notanip"))

    def test_ip(self):
        ip6 = "2001:db8::1"
        self.session6.ip_address = ip6
        self.assertEqual(ip6, FILTER_DICT["ip"](self.session6))
        self.session6.ip_address = ipaddress.ip_address(ip6)
        self.assertEqual(ip6, FILTER_DICT["ip"](self.session6))
        self.session6.ip_address = ipaddress.ip_interface(f"{ip6}/64")
        self.assertEqual(ip6, FILTER_DICT["ip"](self.session6))
        self.assertEqual(ip6, FILTER_DICT["ip"](ip6))
        self.assertEqual(ip6, FILTER_DICT["ip"](f"{ip6}/64"))
        self.assertEqual(ip6, FILTER_DICT["ip"](ipaddress.ip_address(ip6)))
        self.assertEqual(ip6, FILTER_DICT["ip"](ipaddress.ip_interface(f"{ip6}/64")))

        ip4 = "192.0.2.10"
        self.session4.ip_address = ip4
        self.assertEqual(ip4, FILTER_DICT["ip"](self.session4))
        self.session4.ip_address = ipaddress.ip_address(ip4)
        self.assertEqual(ip4, FILTER_DICT["ip"](self.session4))
        self.session4.ip_address = ipaddress.ip_interface(f"{ip4}/24")
        self.assertEqual(ip4, FILTER_DICT["ip"](self.session4))
        self.assertEqual(ip4, FILTER_DICT["ip"](ip4))
        self.assertEqual(ip4, FILTER_DICT["ip"](f"{ip4}/24"))
        self.assertEqual(ip4, FILTER_DICT["ip"](ipaddress.ip_address(ip4)))
        self.assertEqual(ip4, FILTER_DICT["ip"](ipaddress.ip_interface(f"{ip4}/24")))

        self.assertListEqual(
            [ip6, ip4], FILTER_DICT["ip"]([self.session6, self.session4])
        )

        with self.assertRaises(ValueError):
            FILTER_DICT["ip"]("notanip")

    def test_ip_version(self):
        self.assertEqual(6, FILTER_DICT["ip_version"](self.session6))
        self.assertEqual(4, FILTER_DICT["ip_version"](self.session4))

    def test_local_ips(self):
        self.assertEqual(
            Connection.objects.get(pk=self.ixp_connection.pk).ipv4_address,
            FILTER_DICT["local_ips"](
                InternetExchangePeeringSession.objects.get(pk=self.session4.pk)
            ),
        )
        self.assertEqual(
            Connection.objects.get(pk=self.ixp_connection.pk).ipv6_address,
            FILTER_DICT["local_ips"](
                InternetExchangePeeringSession.objects.get(pk=self.session6.pk)
            ),
        )
        self.assertListEqual(
            [
                Connection.objects.get(pk=self.ixp_connection.pk).ipv4_address,
                Connection.objects.get(pk=self.ixp_connection.pk).ipv6_address,
            ],
            FILTER_DICT["local_ips"](InternetExchange.objects.get(pk=self.ixp.pk)),
        )
        self.assertListEqual(
            [Connection.objects.get(pk=self.ixp_connection.pk).ipv6_address],
            FILTER_DICT["local_ips"](InternetExchange.objects.get(pk=self.ixp.pk), 6),
        )
        self.assertListEqual(
            [Connection.objects.get(pk=self.ixp_connection.pk).ipv4_address],
            FILTER_DICT["local_ips"](InternetExchange.objects.get(pk=self.ixp.pk), 4),
        )
        self.assertIsNone(
            FILTER_DICT["local_ips"](Connection.objects.get(pk=self.ixp_connection.pk))
        )

    def test_mac(self):
        self.assertEqual("00:1b:77:49:54:fd", FILTER_DICT["mac"](self.ixp_connection))
        self.assertEqual("00:1b:77:49:54:fd", FILTER_DICT["mac"]("00:1b:77:49:54:fd"))
        self.assertEqual(
            "001b.7749.54fd", FILTER_DICT["mac"]("00:1b:77:49:54:fd", "cisco")
        )
        self.assertEqual(
            "001b774954fd", FILTER_DICT["mac"]("00:1b:77:49:54:fd", "bare")
        )
        with self.assertRaises(ValueError):
            self.assertEqual("", FILTER_DICT["mac"](""))

    def test_inherited_status(self):
        self.assertEqual(
            BGPSessionStatus.ENABLED, FILTER_DICT["inherited_status"](self.session6)
        )
        self.router.status = DeviceStatus.MAINTENANCE
        self.assertEqual(
            BGPSessionStatus.MAINTENANCE, FILTER_DICT["inherited_status"](self.session6)
        )
        self.ixp_connection.status = ConnectionStatus.DISABLED
        # Inherit from connection
        self.assertEqual(
            BGPSessionStatus.DISABLED, FILTER_DICT["inherited_status"](self.session6)
        )
        self.assertEqual(
            DeviceStatus.MAINTENANCE, FILTER_DICT["inherited_status"](self.router)
        )
        self.assertEqual(
            ConnectionStatus.DISABLED,
            FILTER_DICT["inherited_status"](self.ixp_connection),
        )
        # Inherit from router
        self.ixp_connection.status = ConnectionStatus.ENABLED
        self.assertEqual(
            ConnectionStatus.MAINTENANCE,
            FILTER_DICT["inherited_status"](self.ixp_connection),
        )
        self.ixp.status = BGPGroupStatus.MAINTENANCE
        self.assertEqual(
            BGPGroupStatus.MAINTENANCE, FILTER_DICT["inherited_status"](self.ixp)
        )
        # Inherit from IXP
        self.assertEqual(
            ConnectionStatus.MAINTENANCE,
            FILTER_DICT["inherited_status"](self.ixp_connection),
        )
        self.assertEqual(
            BGPSessionStatus.MAINTENANCE, FILTER_DICT["inherited_status"](self.session6)
        )

    def test_max_prefix(self):
        self.assertEqual(100, FILTER_DICT["max_prefix"](self.session6))
        self.assertEqual(0, FILTER_DICT["max_prefix"](self.session4))

    def test_filter(self):
        sessions = InternetExchangePeeringSession.objects.all()
        filtered = FILTER_DICT["filter"](sessions, ip_address__family=6)
        self.assertEqual(4, FILTER_DICT["length"](sessions))
        self.assertEqual(2, FILTER_DICT["length"](filtered))

        policies = [
            RoutingPolicy.objects.get(slug="export-deaggregated-v4"),
            RoutingPolicy.objects.get(slug="export-deaggregated-v6"),
        ]
        filtered = FILTER_DICT["filter"](policies, address_family=6)
        self.assertEqual(1, FILTER_DICT["length"](filtered))

        communities = FILTER_DICT["merge_communities"](self.session6)
        filtered = FILTER_DICT["filter"](communities, type=CommunityType.INGRESS)
        self.assertEqual(1, FILTER_DICT["length"](filtered))
        filtered = FILTER_DICT["filter"](communities, type=CommunityType.EGRESS)
        self.assertEqual(0, FILTER_DICT["length"](filtered))
        filtered = FILTER_DICT["filter"](communities, type=None)
        self.assertEqual(1, FILTER_DICT["length"](filtered))

    def test_get(self):
        ixps = InternetExchange.objects.all()
        self.assertIsInstance(
            FILTER_DICT["get"](ixps, pk=self.ixp.pk), InternetExchange
        )
        sessions = InternetExchangePeeringSession.objects.all()
        self.assertIsInstance(
            FILTER_DICT["get"](sessions, ip_address="2001:db8::1"),
            InternetExchangePeeringSession,
        )
        self.assertEqual(0, len(FILTER_DICT["get"](sessions, ip_address="2001:a::a")))

    def test_unique(self):
        sessions = InternetExchangePeeringSession.objects.all()
        self.assertEqual(
            1, len(FILTER_DICT["unique_items"](sessions, "autonomous_system"))
        )
        self.assertEqual(4, len(FILTER_DICT["unique_items"](sessions, "ip_address")))

    def test_iterate(self):
        routing_policies = RoutingPolicy.objects.all()
        slugs = list(FILTER_DICT["iterate"](routing_policies, "slug"))
        self.assertListEqual([rp.slug for rp in routing_policies], slugs)

    def test_length(self):
        self.assertEqual(6, FILTER_DICT["length"](RoutingPolicy.objects.all()))
        self.assertEqual(0, FILTER_DICT["length"](RoutingPolicy.objects.none()))

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
        self.assertListEqual(
            ["accept-all", "export-supernets"],
            FILTER_DICT["iter_export_policies"](self.session6, field="slug"),
        )
        self.assertListEqual(
            [RoutingPolicy.objects.get(slug="reject-all")],
            FILTER_DICT["iter_export_policies"](self.ixp),
        )
        self.ixp.export_routing_policies.add(
            RoutingPolicy.objects.get(slug="export-deaggregated-v4"),
            RoutingPolicy.objects.get(slug="export-deaggregated-v6"),
        )
        self.assertListEqual(
            [
                RoutingPolicy.objects.get(slug="reject-all"),
                RoutingPolicy.objects.get(slug="export-deaggregated-v6"),
            ],
            FILTER_DICT["iter_export_policies"](self.ixp, family=6),
        )

    def test_iter_import_policies(self):
        self.assertListEqual(
            [RoutingPolicy.objects.get(slug="accept-all")],
            FILTER_DICT["iter_import_policies"](self.session6),
        )
        self.assertListEqual(
            ["accept-all"],
            FILTER_DICT["iter_import_policies"](self.session6, field="slug"),
        )
        self.assertListEqual(
            [RoutingPolicy.objects.get(slug="reject-all")],
            FILTER_DICT["iter_import_policies"](self.ixp),
        )
        self.ixp.import_routing_policies.add(
            RoutingPolicy.objects.get(slug="export-deaggregated-v4"),
            RoutingPolicy.objects.get(slug="export-deaggregated-v6"),
        )
        self.assertListEqual(
            [
                RoutingPolicy.objects.get(slug="reject-all"),
                RoutingPolicy.objects.get(slug="export-deaggregated-v4"),
            ],
            FILTER_DICT["iter_import_policies"](self.ixp, family=4),
        )

    def test_merge_export_policies(self):
        self.assertListEqual(
            [
                RoutingPolicy.objects.get(slug="accept-all"),
                RoutingPolicy.objects.get(slug="export-supernets"),
                RoutingPolicy.objects.get(slug="export-deaggregated-v6"),
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

    def test_communities(self):
        self.assertEqual(1, len(FILTER_DICT["communities"](self.ixp)))
        self.assertEqual(0, len(FILTER_DICT["communities"](self.session6)))
        self.assertEqual(0, len(FILTER_DICT["communities"](self.router)))

    def test_merge_communities(self):
        self.assertEqual(2, len(FILTER_DICT["merge_communities"](self.session6)))

    def test_contact(self):
        self.assertEqual(
            self.contact, FILTER_DICT["contact"](self.a_s, "Contact Role 1")
        )
        self.assertEqual(
            self.contact, FILTER_DICT["contact"](self.session6, "Contact Role 1")
        )
        self.assertIsNone(FILTER_DICT["contact"](self.session6, "test"))
        self.assertRaises(AttributeError, FILTER_DICT["contact"], self.router, "test")

    def connections(self):
        self.assertEqual(1, FILTER_DICT["connections"](self.ixp).count())
        self.assertEqual(1, FILTER_DICT["connections"](self.router).count())
        self.assertRaises(AttributeError, FILTER_DICT["connections"], self.a_s)

    def test_direct_sessions(self):
        self.assertEqual(0, FILTER_DICT["direct_sessions"](self.a_s).count())
        self.assertEqual(0, FILTER_DICT["direct_sessions"](self.router).count())

    def test_ixp_sessions(self):
        tmp_ixp = InternetExchange.objects.create(
            local_autonomous_system=AutonomousSystem.objects.get(asn=64500),
            name="Temp IXP",
            slug="temp-ixp",
        )
        tmp_ixp_connection = Connection.objects.create(
            vlan=10, internet_exchange_point=tmp_ixp, ipv4_address="192.0.10.10"
        )
        InternetExchangePeeringSession.objects.create(
            autonomous_system=self.a_s,
            ixp_connection=tmp_ixp_connection,
            ip_address="192.0.10.1",
        )

        self.assertEqual(5, FILTER_DICT["ixp_sessions"](self.a_s).count())
        self.assertEqual(2, FILTER_DICT["ixp_sessions"](self.a_s, family=6).count())
        self.assertEqual(3, FILTER_DICT["ixp_sessions"](self.a_s, family=4).count())
        self.assertEqual(
            4, FILTER_DICT["ixp_sessions"](self.router, ixp=self.ixp).count()
        )
        self.assertEqual(1, FILTER_DICT["ixp_sessions"](self.a_s, ixp=tmp_ixp).count())
        self.assertEqual(4, FILTER_DICT["ixp_sessions"](self.a_s, ixp=self.ixp).count())

    def test_sessions(self):
        self.assertEqual(4, FILTER_DICT["sessions"](self.ixp).count())
        self.assertEqual(2, FILTER_DICT["sessions"](self.ixp, family=6).count())
        self.assertEqual(2, FILTER_DICT["sessions"](self.ixp, family=4).count())

    def test_route_server(self):
        self.assertEqual(2, FILTER_DICT["route_server"](self.ixp).count())

    def test_direct_peers(self):
        self.assertEqual(0, FILTER_DICT["direct_peers"](self.router).count())

    def test_ixp_peers(self):
        self.assertEqual(1, FILTER_DICT["ixp_peers"](self.router).count())
        self.assertEqual(1, FILTER_DICT["ixp_peers"](self.router, "test-ixp").count())

    def test_prefix_list(self):
        pass

    def test_as_list(self):
        pass

    def test_safe_string(self):
        self.assertEqual("Tele_a_ciu", FILTER_DICT["safe_string"]("Téle_à_çiu"))

    def test_quote(self):
        self.assertEqual('"example"', FILTER_DICT["quote"]("example"))
        self.assertEqual("||example||", FILTER_DICT["quote"]("example", "||"))
        self.assertEqual('"12345"', FILTER_DICT["quote"](12345))
        for i in (None, "", [], {}):
            self.assertEqual("", FILTER_DICT["quote"](i))

    def test_tags(self):
        self.assertEqual(3, FILTER_DICT["tags"](self.a_s).count())
        self.assertEqual(0, FILTER_DICT["tags"](self.ixp).count())

    def test_has_tag(self):
        self.assertEqual(True, FILTER_DICT["has_tag"](self.a_s, "tag-1"))
        self.assertEqual(True, FILTER_DICT["has_tag"](self.a_s, "Tag 1"))
        self.assertEqual(False, FILTER_DICT["has_tag"](self.router, "tag-1"))
        self.assertEqual(False, FILTER_DICT["has_tag"](self.router, "Tag 1"))

    def test_has_not_tag(self):
        self.assertEqual(False, FILTER_DICT["has_not_tag"](self.a_s, "tag-1"))
        self.assertEqual(False, FILTER_DICT["has_not_tag"](self.a_s, "Tag 1"))
        self.assertEqual(True, FILTER_DICT["has_not_tag"](self.router, "tag-1"))
        self.assertEqual(True, FILTER_DICT["has_not_tag"](self.router, "Tag 1"))

    def test_include_template_extension(self):
        Configuration.objects.create(name="test", template="this is a test")
        main = Configuration.objects.create(
            name="main",
            template="{% include_configuration 'test' %} - {% include 'configuration::test' %}",
        )
        self.assertEqual("this is a test - this is a test", main.render({}))

        Email.objects.create(name="test", subject="test", template="this is a test")
        main = Email.objects.create(
            name="main",
            subject="main",
            template="{% include_email 'test' %} - {% include 'email::test' %}",
        )
        self.assertEqual(("main", "this is a test - this is a test"), main.render({}))

        content_type = ContentType.objects.get_for_model(AutonomousSystem)
        ExportTemplate.objects.create(
            name="test", content_type=content_type, template="this is a test"
        )
        main = ExportTemplate.objects.create(
            name="main",
            content_type=content_type,
            template="{% include_exporttemplate 'test' %} - {% include 'exporttemplate::test' %}",
        )
        self.assertEqual("this is a test - this is a test", main.render())

    def test_context_has_key(self):
        self.assertEqual(True, FILTER_DICT["context_has_key"](self.router, "foo"))
        self.assertEqual(False, FILTER_DICT["context_has_key"](self.router, "bar"))

        self.assertEqual(
            True, FILTER_DICT["context_has_key"](self.router, "inside", recursive=True)
        )
        self.assertEqual(
            False,
            FILTER_DICT["context_has_key"](self.router, "inside", recursive=False),
        )

    def test_context_has_not_key(self):
        self.assertEqual(False, FILTER_DICT["context_has_not_key"](self.router, "foo"))
        self.assertEqual(True, FILTER_DICT["context_has_not_key"](self.router, "bar"))
        self.assertEqual(
            False,
            FILTER_DICT["context_has_not_key"](self.router, "inside", recursive=True),
        )
        self.assertEqual(
            True,
            FILTER_DICT["context_has_not_key"](self.router, "inside", recursive=False),
        )

    def test_context_get_key(self):
        self.assertEqual("bar", FILTER_DICT["context_get_key"](self.router, "foo"))
        self.assertEqual(None, FILTER_DICT["context_get_key"](self.router, "bar"))
        self.assertEqual(
            "nope",
            FILTER_DICT["context_get_key"](
                self.router, "inside", default="nope", recursive=False
            ),
        )
        self.assertEqual(
            True,
            FILTER_DICT["context_get_key"](
                self.router, "inside", default="nope", recursive=True
            ),
        )

    def test_as_json(self):
        data = {"foo": "bar"}
        self.assertDictEqual(data, json.loads(FILTER_DICT["as_json"](data)))
        data = 1
        self.assertEqual(data, json.loads(FILTER_DICT["as_json"](data)))
        data = RoutingPolicy.objects.all()
        self.assertIsInstance(json.loads(FILTER_DICT["as_json"](data)), list)
        data = RoutingPolicy.objects.first()
        self.assertIsInstance(json.loads(FILTER_DICT["as_json"](data)), dict)

    def test_as_yaml(self):
        data = {"foo": "bar"}
        self.assertDictEqual(data, yaml.safe_load(FILTER_DICT["as_yaml"](data)))
        data = 1
        self.assertEqual(data, json.loads(FILTER_DICT["as_json"](data)))
        data = RoutingPolicy.objects.all()
        self.assertIsInstance(json.loads(FILTER_DICT["as_json"](data)), list)
        data = RoutingPolicy.objects.first()
        self.assertIsInstance(json.loads(FILTER_DICT["as_json"](data)), dict)

    def test_indent(self):
        data = "a\nb\nc"
        self.assertEqual("  a\n  b\n  c", FILTER_DICT["indent"](data, 2))
        data = "  a\n  b\n  c"
        self.assertEqual("  a\n  b\n  c", FILTER_DICT["indent"](data, 2, reset=True))
        data = "a\nb\nc"
        self.assertEqual("\ta\n\tb\n\tc", FILTER_DICT["indent"](data, 1, chars="\t"))

    def test_routing_policies(self):
        expected = {
            "accept-all",
            "export-supernets",
            "import-known-prefixes",
            "export-deaggregated-v4",
            "export-deaggregated-v6",
            "reject-all",
        }
        policies = FILTER_DICT["routing_policies"](self.router)
        self.assertEqual(expected, {p.slug for p in policies})

        policy_slugs = FILTER_DICT["routing_policies"](self.router, field="slug")
        self.assertEqual(expected, set(policy_slugs))

        ipv6_policies = FILTER_DICT["routing_policies"](self.router, family=6)
        ipv6_slugs = {p.slug for p in ipv6_policies}
        self.assertIn("export-deaggregated-v6", ipv6_slugs)
        self.assertIn("accept-all", ipv6_slugs)
        self.assertNotIn("export-deaggregated-v4", ipv6_slugs)

        ipv6_slugs = set(
            FILTER_DICT["routing_policies"](self.router, field="slug", family=6)
        )
        self.assertIn("export-deaggregated-v6", ipv6_slugs)
        self.assertIn("accept-all", ipv6_slugs)
        self.assertNotIn("export-deaggregated-v4", ipv6_slugs)
