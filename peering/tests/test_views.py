import ipaddress

from bgp.models import Relationship
from net.models import Connection
from utils.testing import ViewTestCases

from ..enums import BGPSessionStatus, RoutingPolicyType
from ..models import *


class AutonomousSystemTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = AutonomousSystem

    test_bulk_edit_objects = None

    @classmethod
    def setUpTestData(cls):
        AutonomousSystem.objects.bulk_create(
            [
                AutonomousSystem(asn=64501, name="Autonomous System 1"),
                AutonomousSystem(asn=64502, name="Autonomous System 2"),
                AutonomousSystem(asn=64503, name="Autonomous System 3"),
            ]
        )

        cls.form_data = {
            "asn": 64504,
            "name": "Autonomous System 4",
            "name_peeringdb_sync": False,
            "export_routing_policies": [],
            "import_routing_policies": [],
            "ipv4_max_prefixes": 0,
            "ipv4_max_prefixes_peeringdb_sync": False,
            "ipv6_max_prefixes": 0,
            "ipv6_max_prefixes_peeringdb_sync": False,
            "irr_as_set": None,
            "irr_as_set_peeringdb_sync": False,
            "comments": "",
            "affiliated": False,
            "tags": [],
        }


class BGPGroupTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = BGPGroup

    @classmethod
    def setUpTestData(cls):
        BGPGroup.objects.bulk_create(
            [
                BGPGroup(name="BGP Group 1", slug="bgp-group-1"),
                BGPGroup(name="BGP Group 2", slug="bgp-group-2"),
                BGPGroup(name="BGP Group 3", slug="bgp-group-3"),
            ]
        )

        cls.form_data = {
            "name": "BGP Group 4",
            "slug": "bgp-group-4",
            "communities": [],
            "export_routing_policies": [],
            "import_routing_policies": [],
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {"description": "New description"}


class DirectPeeringSessionTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = DirectPeeringSession

    @classmethod
    def setUpTestData(cls):
        local_as = AutonomousSystem.objects.create(
            asn=64501, name="Autonomous System 1", affiliated=True
        )
        a_s = AutonomousSystem.objects.create(asn=64502, name="Autonomous System 2")
        relationship_private_peering = Relationship.objects.create(
            name="Private Peering", slug="private-peering"
        )
        DirectPeeringSession.objects.bulk_create(
            [
                DirectPeeringSession(
                    local_autonomous_system=local_as,
                    autonomous_system=a_s,
                    ip_address="192.0.2.1",
                    relationship=relationship_private_peering,
                ),
                DirectPeeringSession(
                    local_autonomous_system=local_as,
                    autonomous_system=a_s,
                    ip_address="192.0.2.2",
                    relationship=relationship_private_peering,
                ),
                DirectPeeringSession(
                    local_autonomous_system=local_as,
                    autonomous_system=a_s,
                    ip_address="192.0.2.3",
                    relationship=relationship_private_peering,
                ),
            ]
        )

        cls.form_data = {
            "local_autonomous_system": local_as.pk,
            "local_ip_address": None,
            "autonomous_system": a_s.pk,
            "ip_address": ipaddress.ip_interface("2001:db8::4/128"),
            "status": BGPSessionStatus.ENABLED,
            "multihop_ttl": 1,
            "relationship": relationship_private_peering.pk,
            "password": None,
            "encrypted_password": None,
            "bgp_group": None,
            "router": None,
            "export_routing_policies": [],
            "import_routing_policies": [],
            "bgp_state": None,
            "last_established_state": None,
            "accepted_prefix_count": 0,
            "advertised_prefix_count": 0,
            "received_prefix_count": 0,
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {
            "enabled": BGPSessionStatus.DISABLED,
            "comments": "New comments",
        }


class InternetExchangeTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = InternetExchange

    @classmethod
    def setUpTestData(cls):
        local_as = AutonomousSystem.objects.create(
            asn=64501, name="Autonomous System 1", affiliated=True
        )
        InternetExchange.objects.bulk_create(
            [
                InternetExchange(
                    name="Internet Exchange 1",
                    slug="ix-1",
                    local_autonomous_system=local_as,
                ),
                InternetExchange(
                    name="Internet Exchange 2",
                    slug="ix-2",
                    local_autonomous_system=local_as,
                ),
                InternetExchange(
                    name="Internet Exchange 3",
                    slug="ix-3",
                    local_autonomous_system=local_as,
                ),
            ]
        )

        cls.form_data = {
            "peeringdb_ixlan": None,
            "name": "Internet Exchange 4",
            "slug": "ix-4",
            "local_autonomous_system": local_as.pk,
            "communities": [],
            "export_routing_policies": [],
            "import_routing_policies": [],
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {"description": "New description"}


class InternetExchangePeeringSessionTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = InternetExchangePeeringSession

    @classmethod
    def setUpTestData(cls):
        local_as = AutonomousSystem.objects.create(
            asn=64501, name="Autonomous System 1", affiliated=True
        )
        cls.a_s = AutonomousSystem.objects.create(asn=64502, name="Autonomous System 2")
        cls.ixp = InternetExchange.objects.create(
            name="Internet Exchange 1", slug="ix-1", local_autonomous_system=local_as
        )
        cls.ixp_connection = Connection.objects.create(
            vlan=2000, internet_exchange_point=cls.ixp
        )
        InternetExchangePeeringSession.objects.bulk_create(
            [
                InternetExchangePeeringSession(
                    autonomous_system=cls.a_s,
                    ixp_connection=cls.ixp_connection,
                    ip_address="192.0.2.1",
                ),
                InternetExchangePeeringSession(
                    autonomous_system=cls.a_s,
                    ixp_connection=cls.ixp_connection,
                    ip_address="192.0.2.2",
                ),
                InternetExchangePeeringSession(
                    autonomous_system=cls.a_s,
                    ixp_connection=cls.ixp_connection,
                    ip_address="192.0.2.3",
                ),
            ]
        )

        cls.form_data = {
            "autonomous_system": cls.a_s.pk,
            "internet_exchange": cls.ixp.pk,
            "ixp_connection": cls.ixp_connection.pk,
            "ip_address": ipaddress.ip_address("2001:db8::4"),
            "multihop_ttl": 1,
            "password": None,
            "encrypted_password": None,
            "is_route_server": False,
            "enabled": True,
            "export_routing_policies": [],
            "import_routing_policies": [],
            "bgp_state": None,
            "last_established_state": None,
            "accepted_prefix_count": 0,
            "advertised_prefix_count": 0,
            "received_prefix_count": 0,
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {
            "is_route_server": True,
            "enabled": False,
            "comments": "New comments",
        }


class RoutingPolicyTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = RoutingPolicy

    @classmethod
    def setUpTestData(cls):
        RoutingPolicy.objects.bulk_create(
            [
                RoutingPolicy(
                    name="Routing Policy 1",
                    slug="routing-policy-1",
                    type=RoutingPolicyType.EXPORT,
                    weight=0,
                ),
                RoutingPolicy(
                    name="Routing Policy 2",
                    slug="routing-policy-2",
                    type=RoutingPolicyType.IMPORT,
                    weight=0,
                ),
                RoutingPolicy(
                    name="Routing Policy 3",
                    slug="routing-policy-3",
                    type=RoutingPolicyType.IMPORT_EXPORT,
                    weight=0,
                ),
            ]
        )

        cls.form_data = {
            "name": "Routing Policy 4",
            "slug": "routing-policy-4",
            "type": RoutingPolicyType.IMPORT,
            "address_family": 6,
            "weight": 1,
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {"weight": 10, "description": "New description"}
