import ipaddress

from django.core import mail
from django.db import transaction
from django.urls.exceptions import NoReverseMatch

from net.models import Connection
from peering.enums import BGPRelationship, CommunityType, DeviceState, RoutingPolicyType
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
from utils.testing import ViewTestCases


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
            "bgp_session_states_update": None,
            "check_bgp_session_states": False,
            "communities": [],
            "export_routing_policies": [],
            "import_routing_policies": [],
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {"comments": "New comments"}


class CommunityTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Community

    @classmethod
    def setUpTestData(cls):
        Community.objects.bulk_create(
            [
                Community(name="Community 1", slug="community-1", value="64500:1"),
                Community(name="Community 2", slug="community-2", value="64500:2"),
                Community(name="Community 3", slug="community-3", value="64500:3"),
            ]
        )

        cls.form_data = {
            "name": "Community 4",
            "slug": "community-4",
            "value": "64500:4",
            "type": CommunityType.INGRESS,
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {"comments": "New comments"}


class ConfigurationTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Configuration

    test_bulk_edit_objects = None

    @classmethod
    def setUpTestData(cls):
        Configuration.objects.bulk_create(
            [
                Configuration(name="Configuration 1", template="Configuration 1"),
                Configuration(name="Configuration 2", template="Configuration 2"),
                Configuration(name="Configuration 3", template="Configuration 3"),
            ]
        )

        cls.form_data = {
            "name": "Configuration 4",
            "template": "Configuration 4",
            "comments": "",
            "tags": [],
        }


class DirectPeeringSessionTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = DirectPeeringSession

    @classmethod
    def setUpTestData(cls):
        local_as = AutonomousSystem.objects.create(
            asn=64501, name="Autonomous System 1", affiliated=True
        )
        a_s = AutonomousSystem.objects.create(asn=64502, name="Autonomous System 2")
        DirectPeeringSession.objects.bulk_create(
            [
                DirectPeeringSession(
                    local_autonomous_system=local_as,
                    autonomous_system=a_s,
                    ip_address="192.0.2.1",
                    relationship=BGPRelationship.PRIVATE_PEERING,
                ),
                DirectPeeringSession(
                    local_autonomous_system=local_as,
                    autonomous_system=a_s,
                    ip_address="192.0.2.2",
                    relationship=BGPRelationship.PRIVATE_PEERING,
                ),
                DirectPeeringSession(
                    local_autonomous_system=local_as,
                    autonomous_system=a_s,
                    ip_address="192.0.2.3",
                    relationship=BGPRelationship.PRIVATE_PEERING,
                ),
            ]
        )

        cls.form_data = {
            "local_autonomous_system": local_as.pk,
            "local_ip_address": None,
            "autonomous_system": a_s.pk,
            "ip_address": ipaddress.ip_address("2001:db8::4"),
            "multihop_ttl": 1,
            "relationship": BGPRelationship.PRIVATE_PEERING,
            "password": None,
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
            "tags": [],
        }
        cls.bulk_edit_data = {"enabled": False, "comments": "New comments"}


class EmailTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Email

    test_bulk_edit_objects = None

    @classmethod
    def setUpTestData(cls):
        Email.objects.bulk_create(
            [
                Email(
                    name="E-mail 1",
                    subject="E-mail subject 1",
                    template="E-mail template 1",
                ),
                Email(
                    name="E-mail 2",
                    subject="E-mail subject 2",
                    template="E-mail template 2",
                ),
                Email(
                    name="E-mail 3",
                    subject="E-mail subject 3",
                    template="E-mail template 3",
                ),
            ]
        )

        cls.form_data = {
            "name": "E-mail 4",
            "subject": "E-mail subject 4",
            "template": "E-mail template 4",
            "comments": "",
            "tags": [],
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
            "bgp_session_states_update": None,
            "check_bgp_session_states": False,
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {"comments": "New comments"}


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


class RouterTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Router

    @classmethod
    def setUpTestData(cls):
        local_as = AutonomousSystem.objects.create(
            asn=64500,
            name="Autonomous System",
            affiliated=True,
        )

        Router.objects.bulk_create(
            [
                Router(
                    name="Router 1",
                    hostname="router1.example.net",
                    local_autonomous_system=local_as,
                    device_state=DeviceState.ENABLED,
                ),
                Router(
                    name="Router 2",
                    hostname="router2.example.net",
                    local_autonomous_system=local_as,
                    device_state=DeviceState.ENABLED,
                ),
                Router(
                    name="Router 3",
                    hostname="router3.example.net",
                    local_autonomous_system=local_as,
                    device_state=DeviceState.ENABLED,
                ),
            ]
        )

        cls.form_data = {
            "name": "Router 4",
            "hostname": "router4.example.net",
            "configuration_template": None,
            "local_autonomous_system": local_as.pk,
            "encrypt_passwords": False,
            "platform": None,
            "device_state": DeviceState.ENABLED,
            "netbox_device_id": 0,
            "use_netbox": False,
            "comments": "",
            "tags": [],
            "napalm_args": None,
            "napalm_password": None,
            "napalm_timeout": 30,
            "napalm_username": "",
        }
        cls.bulk_edit_data = {"comments": "New comments"}


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
        cls.bulk_edit_data = {"weight": 10, "comments": "New comments"}
