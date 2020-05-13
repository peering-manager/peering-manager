import ipaddress

from django.core import mail
from django.db import transaction
from django.urls.exceptions import NoReverseMatch

from peering.constants import (
    BGP_RELATIONSHIP_PRIVATE_PEERING,
    COMMUNITY_TYPE_INGRESS,
    PLATFORM_JUNOS,
    ROUTING_POLICY_TYPE_IMPORT,
    ROUTING_POLICY_TYPE_IMPORT_EXPORT,
    ROUTING_POLICY_TYPE_EXPORT,
    TEMPLATE_TYPE_CONFIGURATION,
    TEMPLATE_TYPE_EMAIL,
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

from utils.testing import StandardTestCases


class AutonomousSystemTestCase(StandardTestCases.Views):
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
            "contact_email": "",
            "contact_name": "",
            "contact_phone": "",
            "export_routing_policies": [],
            "import_routing_policies": [],
            "ipv4_max_prefixes": 0,
            "ipv4_max_prefixes_peeringdb_sync": False,
            "ipv6_max_prefixes": 0,
            "ipv6_max_prefixes_peeringdb_sync": False,
            "irr_as_set": None,
            "irr_as_set_peeringdb_sync": False,
            "potential_internet_exchange_peering_sessions": [],
            "comments": "",
            "tags": "",
        }


class BGPGroupTestCase(StandardTestCases.Views):
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
            "bgp_session_states_update": None,
            "check_bgp_session_states": False,
            "communities": [],
            "export_routing_policies": [],
            "import_routing_policies": [],
            "comments": "",
            "tags": "",
        }
        cls.bulk_edit_data = {"comments": "New comments"}


class CommunityTestCase(StandardTestCases.Views):
    model = Community

    @classmethod
    def setUpTestData(cls):
        Community.objects.bulk_create(
            [
                Community(name="Community 1", value="64500:1"),
                Community(name="Community 2", value="64500:2"),
                Community(name="Community 3", value="64500:3"),
            ]
        )

        cls.form_data = {
            "name": "Community 4",
            "value": "64500:4",
            "type": COMMUNITY_TYPE_INGRESS,
            "comments": "",
            "tags": "",
        }
        cls.bulk_edit_data = {"comments": "New comments"}


class DirectPeeringSessionTestCase(StandardTestCases.Views):
    model = DirectPeeringSession

    @classmethod
    def setUpTestData(cls):
        cls.a_s = AutonomousSystem.objects.create(asn=64501, name="Autonomous System 1")
        DirectPeeringSession.objects.bulk_create(
            [
                DirectPeeringSession(
                    local_asn=64500,
                    autonomous_system=cls.a_s,
                    ip_address="192.0.2.1",
                    relationship=BGP_RELATIONSHIP_PRIVATE_PEERING,
                ),
                DirectPeeringSession(
                    local_asn=64500,
                    autonomous_system=cls.a_s,
                    ip_address="192.0.2.2",
                    relationship=BGP_RELATIONSHIP_PRIVATE_PEERING,
                ),
                DirectPeeringSession(
                    local_asn=64500,
                    autonomous_system=cls.a_s,
                    ip_address="192.0.2.3",
                    relationship=BGP_RELATIONSHIP_PRIVATE_PEERING,
                ),
            ]
        )

        cls.form_data = {
            "local_asn": 64500,
            "local_ip_address": None,
            "autonomous_system": cls.a_s.pk,
            "ip_address": ipaddress.ip_address("2001:db8::4"),
            "multihop_ttl": 1,
            "relationship": BGP_RELATIONSHIP_PRIVATE_PEERING,
            "password": "",
            "encrypted_password": None,
            "enabled": True,
            "bgp_group": None,
            "router": None,
            "export_routing_policies": [],
            "import_routing_policies": [],
            "bgp_state": None,
            "last_established_state": None,
            "advertised_prefix_count": 0,
            "received_prefix_count": 0,
            "comments": "",
            "tags": "",
        }
        cls.bulk_edit_data = {"enabled": False, "comments": "New comments"}


class InternetExchangeTestCase(StandardTestCases.Views):
    model = InternetExchange

    @classmethod
    def setUpTestData(cls):
        InternetExchange.objects.bulk_create(
            [
                InternetExchange(name="Internet Exchange 1", slug="ix-1"),
                InternetExchange(name="Internet Exchange 2", slug="ix-2"),
                InternetExchange(name="Internet Exchange 3", slug="ix-3"),
            ]
        )

        cls.form_data = {
            "name": "Internet Exchange 4",
            "slug": "ix-4",
            "ipv4_address": None,
            "ipv6_address": None,
            "router": None,
            "communities": [],
            "export_routing_policies": [],
            "import_routing_policies": [],
            "bgp_session_states_update": None,
            "check_bgp_session_states": False,
            "peeringdb_id": 0,
            "comments": "",
            "tags": "",
        }
        cls.bulk_edit_data = {"comments": "New comments"}


class InternetExchangePeeringSessionTestCase(StandardTestCases.Views):
    model = InternetExchangePeeringSession

    @classmethod
    def setUpTestData(cls):
        cls.a_s = AutonomousSystem.objects.create(asn=64501, name="Autonomous System 1")
        cls.ix = InternetExchange.objects.create(
            name="Internet Exchange 1", slug="ix-1"
        )
        InternetExchangePeeringSession.objects.bulk_create(
            [
                InternetExchangePeeringSession(
                    autonomous_system=cls.a_s,
                    internet_exchange=cls.ix,
                    ip_address="192.0.2.1",
                ),
                InternetExchangePeeringSession(
                    autonomous_system=cls.a_s,
                    internet_exchange=cls.ix,
                    ip_address="192.0.2.2",
                ),
                InternetExchangePeeringSession(
                    autonomous_system=cls.a_s,
                    internet_exchange=cls.ix,
                    ip_address="192.0.2.3",
                ),
            ]
        )

        cls.form_data = {
            "autonomous_system": cls.a_s.pk,
            "internet_exchange": cls.ix.pk,
            "ip_address": ipaddress.ip_address("2001:db8::4"),
            "multihop_ttl": 1,
            "password": "",
            "encrypted_password": None,
            "is_route_server": False,
            "enabled": True,
            "export_routing_policies": [],
            "import_routing_policies": [],
            "bgp_state": None,
            "last_established_state": None,
            "advertised_prefix_count": 0,
            "received_prefix_count": 0,
            "comments": "",
            "tags": "",
        }
        cls.bulk_edit_data = {
            "is_route_server": True,
            "enabled": False,
            "comments": "New comments",
        }


class RouterTestCase(StandardTestCases.Views):
    model = Router

    @classmethod
    def setUpTestData(cls):
        Router.objects.bulk_create(
            [
                Router(name="Router 1", hostname="router1.example.net"),
                Router(name="Router 2", hostname="router2.example.net"),
                Router(name="Router 3", hostname="router3.example.net"),
            ]
        )

        cls.form_data = {
            "name": "Router 4",
            "hostname": "router4.example.net",
            "configuration_template": None,
            "encrypt_passwords": False,
            "platform": PLATFORM_JUNOS,
            "netbox_device_id": 0,
            "use_netbox": False,
            "comments": "",
            "tags": "",
            "napalm_args": None,
            "napalm_password": "",
            "napalm_timeout": 30,
            "napalm_username": "",
        }
        cls.bulk_edit_data = {"platform": PLATFORM_JUNOS, "comments": "New comments"}


class RoutingPolicyTestCase(StandardTestCases.Views):
    model = RoutingPolicy

    @classmethod
    def setUpTestData(cls):
        RoutingPolicy.objects.bulk_create(
            [
                RoutingPolicy(
                    name="Routing Policy 1",
                    slug="routing-policy-1",
                    type=ROUTING_POLICY_TYPE_EXPORT,
                    weight=0,
                ),
                RoutingPolicy(
                    name="Routing Policy 2",
                    slug="routing-policy-2",
                    type=ROUTING_POLICY_TYPE_IMPORT,
                    weight=0,
                ),
                RoutingPolicy(
                    name="Routing Policy 3",
                    slug="routing-policy-3",
                    type=ROUTING_POLICY_TYPE_IMPORT_EXPORT,
                    weight=0,
                ),
            ]
        )

        cls.form_data = {
            "name": "Routing Policy 4",
            "slug": "routing-policy-4",
            "type": ROUTING_POLICY_TYPE_IMPORT,
            "address_family": 6,
            "weight": 1,
            "comments": "",
            "tags": "",
        }
        cls.bulk_edit_data = {"weight": 10, "comments": "New comments"}


class TemplateTestCase(StandardTestCases.Views):
    model = Template

    test_bulk_edit_objects = None

    @classmethod
    def setUpTestData(cls):
        Template.objects.bulk_create(
            [
                Template(
                    name="Template 1",
                    type=TEMPLATE_TYPE_CONFIGURATION,
                    template="Template 1",
                ),
                Template(
                    name="Template 2",
                    type=TEMPLATE_TYPE_CONFIGURATION,
                    template="Template 2",
                ),
                Template(
                    name="Template 3",
                    type=TEMPLATE_TYPE_CONFIGURATION,
                    template="Template 3",
                ),
            ]
        )

        cls.form_data = {
            "name": "Routing Policy 4",
            "type": TEMPLATE_TYPE_EMAIL,
            "template": "Template 4",
            "comments": "",
            "tags": "",
        }
