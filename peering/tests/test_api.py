from unittest.mock import patch

from django.urls import reverse
from rest_framework import status

from bgp.models import Relationship
from devices.models import Configuration, Platform
from net.models import Connection
from utils.testing import APITestCase, APIViewTestCases

from ..constants import *
from ..enums import BGPSessionStatus, CommunityType, DeviceStatus, RoutingPolicyType
from ..models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from .mocked_data import load_peeringdb_data, mocked_subprocess_popen


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("peering-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AutonomousSystemTest(APIViewTestCases.View):
    model = AutonomousSystem
    brief_fields = [
        "id",
        "url",
        "display",
        "asn",
        "name",
        "ipv6_max_prefixes",
        "ipv4_max_prefixes",
    ]
    create_data = [
        {"asn": 64541, "name": "Test 1"},
        {"asn": 64542, "name": "Test 2"},
        {"asn": 64543, "name": "Test 3"},
    ]
    bulk_update_data = {"comments": "Awesome peer"}

    @classmethod
    def setUpTestData(cls):
        AutonomousSystem.objects.bulk_create(
            [
                AutonomousSystem(asn=65536, name="Example 1", irr_as_set="AS-MOCKED"),
                AutonomousSystem(
                    asn=64496, name="Example 2", irr_as_set="AS-EXAMPLE-2"
                ),
                AutonomousSystem(
                    asn=64497, name="Example 3", irr_as_set="AS-EXAMPLE-3"
                ),
            ]
        )
        cls.autonomous_system = AutonomousSystem.objects.get(asn=65536)
        load_peeringdb_data()

    def test_poll_bgp_sessions(self):
        url = reverse(
            "peering-api:autonomoussystem-poll-bgp-sessions",
            kwargs={"pk": self.autonomous_system.pk},
        )
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)

    def test_synchronise_with_peeringdb(self):
        autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Test", irr_as_set="AS-TEST"
        )
        url = reverse(
            "peering-api:autonomoussystem-sync-with-peeringdb",
            kwargs={"pk": autonomous_system.pk},
        )
        response = self.client.post(url, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)

    def test_get_irr_as_set_prefixes(self):
        with patch("peering.subprocess.Popen", side_effect=mocked_subprocess_popen):
            url = reverse(
                "peering-api:autonomoussystem-as-set-prefixes",
                kwargs={"pk": self.autonomous_system.pk},
            )
            response = self.client.get(url, format="json", **self.header)
            self.assertHttpStatus(response, status.HTTP_200_OK)
            self.assertEqual(len(response.data["ipv6"]), 1)
            self.assertEqual(len(response.data["ipv4"]), 1)

    def test_shared_internet_exchanges(self):
        local_as = AutonomousSystem.objects.create(
            asn=65535, name="Local", irr_as_set="AS-LOCAL", affiliated=True
        )
        self.user.preferences.set("context.as", local_as.pk, commit=True)
        url = reverse(
            "peering-api:autonomoussystem-shared-ixps",
            kwargs={"pk": self.autonomous_system.pk},
        )
        response = self.client.get(url, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class BGPGroupTest(APIViewTestCases.View):
    model = BGPGroup
    brief_fields = ["id", "url", "display", "name", "slug", "status"]
    create_data = [
        {"name": "Test 1", "slug": "test-1"},
        {"name": "Test 2", "slug": "test-2"},
        {"name": "Test 3", "slug": "test-3"},
    ]
    bulk_update_data = {"description": "Awesome group"}

    @classmethod
    def setUpTestData(cls):
        BGPGroup.objects.bulk_create(
            [
                BGPGroup(name="Example 1", slug="example-1"),
                BGPGroup(name="Example 2", slug="example-2"),
                BGPGroup(name="Example 3", slug="example-3"),
            ]
        )

    def test_poll_bgp_sessions(self):
        url = reverse(
            "peering-api:bgpgroup-poll-bgp-sessions",
            kwargs={"pk": BGPGroup.objects.get(slug="example-1").pk},
        )
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)


class CommunityTest(APIViewTestCases.View):
    model = Community
    brief_fields = ["id", "url", "display", "name", "slug", "value", "type"]
    create_data = [
        {
            "name": "Test1",
            "slug": "test1",
            "value": "64500:11",
            "type": CommunityType.EGRESS,
        },
        {
            "name": "Test2",
            "slug": "test2",
            "value": "64500:12",
            "type": CommunityType.EGRESS,
        },
        {
            "name": "Test3",
            "slug": "test3",
            "value": "64500:13",
            "type": CommunityType.EGRESS,
        },
    ]
    bulk_update_data = {"description": "Awesome community"}

    @classmethod
    def setUpTestData(cls):
        Community.objects.bulk_create(
            [
                Community(
                    name="Example 1",
                    slug="example-1",
                    value="64500:1",
                    type=CommunityType.EGRESS,
                ),
                Community(
                    name="Example 2",
                    slug="example-2",
                    value="64500:2",
                    type=CommunityType.EGRESS,
                ),
                Community(
                    name="Example 3",
                    slug="example-3",
                    value="64500:3",
                    type=CommunityType.EGRESS,
                ),
            ]
        )


class DirectPeeringSessionTest(APIViewTestCases.View):
    model = DirectPeeringSession
    brief_fields = ["id", "url", "display", "ip_address", "status"]
    bulk_update_data = {"status": BGPSessionStatus.DISABLED}

    @classmethod
    def setUpTestData(cls):
        local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        autonomous_system = AutonomousSystem.objects.create(asn=64500, name="Dummy")
        relationship_private_peering = Relationship.objects.create(
            name="Private Peering", slug="private-peering"
        )
        DirectPeeringSession.objects.bulk_create(
            [
                DirectPeeringSession(
                    local_autonomous_system=local_autonomous_system,
                    autonomous_system=autonomous_system,
                    relationship=relationship_private_peering,
                    ip_address="2001:db8::1",
                    password="mypassword",
                ),
                DirectPeeringSession(
                    local_autonomous_system=local_autonomous_system,
                    autonomous_system=autonomous_system,
                    relationship=relationship_private_peering,
                    ip_address="2001:db8::2",
                ),
                DirectPeeringSession(
                    local_autonomous_system=local_autonomous_system,
                    autonomous_system=autonomous_system,
                    relationship=relationship_private_peering,
                    ip_address="2001:db8::3",
                ),
            ]
        )
        cls.create_data = [
            {
                "service_reference": "PNI-0001",
                "local_autonomous_system": local_autonomous_system.pk,
                "autonomous_system": autonomous_system.pk,
                "relationship": relationship_private_peering.pk,
                "ip_address": "198.51.100.1/32",
            },
            {
                "local_autonomous_system": local_autonomous_system.pk,
                "autonomous_system": autonomous_system.pk,
                "relationship": relationship_private_peering.pk,
                "ip_address": "198.51.100.2/32",
            },
            {
                "local_autonomous_system": local_autonomous_system.pk,
                "autonomous_system": autonomous_system.pk,
                "relationship": relationship_private_peering.pk,
                "ip_address": "198.51.100.3/32",
            },
        ]


class InternetExchangeTest(APIViewTestCases.View):
    model = InternetExchange
    brief_fields = ["id", "url", "display", "name", "slug", "status"]
    bulk_update_data = {"description": "Awesome IXP"}

    @classmethod
    def setUpTestData(cls):
        cls.local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        InternetExchange.objects.bulk_create(
            [
                InternetExchange(
                    name="Example 1",
                    slug="example-1",
                    local_autonomous_system=cls.local_autonomous_system,
                ),
                InternetExchange(
                    name="Example 2",
                    slug="example-2",
                    local_autonomous_system=cls.local_autonomous_system,
                ),
                InternetExchange(
                    name="Example 3",
                    slug="example-3",
                    local_autonomous_system=cls.local_autonomous_system,
                ),
            ]
        )
        cls.internet_exchange = InternetExchange.objects.get(slug="example-1")
        cls.create_data = [
            {
                "name": "Test1",
                "slug": "test1",
                "local_autonomous_system": cls.local_autonomous_system.pk,
            },
            {
                "name": "Test2",
                "slug": "test2",
                "local_autonomous_system": cls.local_autonomous_system.pk,
            },
            {
                "name": "Test3",
                "slug": "test3",
                "local_autonomous_system": cls.local_autonomous_system.pk,
            },
        ]

    def test_available_peers(self):
        url = reverse(
            "peering-api:internetexchange-available-peers",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.get(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)

    def test_import_sessions(self):
        url = reverse(
            "peering-api:internetexchange-import-sessions",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)

    def test_prefixes(self):
        url = reverse(
            "peering-api:internetexchange-prefixes",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.get(url, **self.header)

        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertDictEqual(response.data, {})

    def test_poll_bgp_sessions(self):
        url = reverse(
            "peering-api:internetexchange-poll-bgp-sessions",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)


class InternetExchangePeeringSessionTest(APIViewTestCases.View):
    model = InternetExchangePeeringSession
    brief_fields = ["id", "url", "display", "ip_address", "status", "is_route_server"]
    bulk_update_data = {"status": BGPSessionStatus.DISABLED}

    @classmethod
    def setUpTestData(cls):
        local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        autonomous_system = AutonomousSystem.objects.create(asn=64500, name="Dummy")
        ixp = InternetExchange.objects.create(
            name="Test", slug="test", local_autonomous_system=local_autonomous_system
        )
        ixp_connection = Connection.objects.create(
            vlan=2000, internet_exchange_point=ixp
        )

        InternetExchangePeeringSession.objects.bulk_create(
            [
                InternetExchangePeeringSession(
                    autonomous_system=autonomous_system,
                    ixp_connection=ixp_connection,
                    ip_address="2001:db8::1",
                    password="mypassword",
                ),
                InternetExchangePeeringSession(
                    autonomous_system=autonomous_system,
                    ixp_connection=ixp_connection,
                    ip_address="2001:db8::2",
                ),
                InternetExchangePeeringSession(
                    autonomous_system=autonomous_system,
                    ixp_connection=ixp_connection,
                    ip_address="2001:db8::3",
                ),
            ]
        )
        cls.create_data = [
            {
                "service_reference": "IXP-0001",
                "autonomous_system": autonomous_system.pk,
                "ixp_connection": ixp_connection.pk,
                "ip_address": "198.51.100.1",
            },
            {
                "autonomous_system": autonomous_system.pk,
                "ixp_connection": ixp_connection.pk,
                "ip_address": "198.51.100.2",
            },
            {
                "autonomous_system": autonomous_system.pk,
                "ixp_connection": ixp_connection.pk,
                "ip_address": "198.51.100.3",
            },
        ]


class RouterTest(APIViewTestCases.View):
    model = Router
    brief_fields = ["id", "url", "display", "name", "hostname"]
    bulk_update_data = {"status": DeviceStatus.MAINTENANCE}

    @classmethod
    def setUpTestData(cls):
        cls.local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        cls.platform = Platform.objects.create(name="No Bugs OS", slug="nobugsos")
        cls.template = Configuration.objects.create(
            name="Test", template="Nothing useful"
        )
        Router.objects.bulk_create(
            [
                Router(
                    name="Example 1",
                    hostname="1.example.com",
                    status=DeviceStatus.ENABLED,
                    configuration_template=cls.template,
                    local_autonomous_system=cls.local_autonomous_system,
                ),
                Router(
                    name="Example 2",
                    hostname="2.example.com",
                    status=DeviceStatus.ENABLED,
                    configuration_template=cls.template,
                    local_autonomous_system=cls.local_autonomous_system,
                ),
                Router(
                    name="Example 3",
                    hostname="3.example.com",
                    status=DeviceStatus.ENABLED,
                    configuration_template=cls.template,
                    local_autonomous_system=cls.local_autonomous_system,
                ),
            ]
        )
        cls.router = Router.objects.get(hostname="1.example.com")
        cls.create_data = [
            {
                "name": "Test 1",
                "hostname": "test1.example.com",
                "status": DeviceStatus.ENABLED,
                "configuration_template": cls.template.pk,
                "local_autonomous_system": cls.local_autonomous_system.pk,
                "platform": cls.platform.pk,
            },
            {
                "name": "Test 2",
                "hostname": "test2.example.com",
                "status": DeviceStatus.MAINTENANCE,
                "configuration_template": cls.template.pk,
                "local_autonomous_system": cls.local_autonomous_system.pk,
                "platform": cls.platform.pk,
            },
            {
                "name": "Test 3",
                "hostname": "test3.example.com",
                "status": DeviceStatus.DISABLED,
                "configuration_template": cls.template.pk,
                "local_autonomous_system": cls.local_autonomous_system.pk,
                "platform": cls.platform.pk,
            },
        ]

    def test_configuration(self):
        url = reverse("peering-api:router-configuration", kwargs={"pk": self.router.pk})
        response = self.client.get(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)

    def test_poll_bgp_sessions(self):
        url = reverse(
            "peering-api:router-poll-bgp-sessions", kwargs={"pk": self.router.pk}
        )
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)

    def test_test_napalm_connection(self):
        url = reverse(
            "peering-api:router-test-napalm-connection", kwargs={"pk": self.router.pk}
        )
        response = self.client.get(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)

    def test_update_from_netbox(self):
        url = reverse("peering-api:router-update-from-netbox")
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(
            url, **self.header, data={"event": "created"}, format="json"
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(
            url, **self.header, data={"data": {}}, format="json"
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

        data = {
            "event": "created",
            "data": {
                "id": 1,
                "url": "/api/dcim/devices/1/",
                "display": "router.example.net",
                "name": "router.example.net",
                "device_role": {
                    "id": 7,
                    "url": "/api/dcim/device-roles/7/",
                    "display": "Router",
                    "name": "Router",
                    "slug": "router",
                },
                "platform": {
                    "id": 9,
                    "url": "/api/dcim/platforms/9/",
                    "display": "Malfunctioning OS",
                    "name": "Malfunctioning OS",
                    "slug": "malfunctioning-os",
                },
                "status": {"value": "active", "label": "Active"},
                "local_context_data": None,
                "tags": [],
            },
        }
        response = self.client.post(url, **self.header, data=data, format="json")
        self.assertHttpStatus(response, status.HTTP_501_NOT_IMPLEMENTED)

        data = {
            "event": "created",
            "data": {
                "id": 1,
                "url": "/api/dcim/devices/1/",
                "display": "router.example.net",
                "name": "router.example.net",
                "device_role": {
                    "id": 7,
                    "url": "/api/dcim/device-roles/7/",
                    "display": "Router",
                    "name": "Router",
                    "slug": "router",
                },
                "platform": {
                    "id": 3,
                    "url": "/api/dcim/platforms/3/",
                    "display": "Juniper Junos",
                    "name": "Juniper Junos",
                    "slug": "juniper-junos",
                },
                "status": {"value": "active", "label": "Active"},
                "local_context_data": None,
                "tags": [],
            },
        }
        response = self.client.post(url, **self.header, data=data, format="json")
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(Router.objects.get(netbox_device_id=1).status, "enabled")

        data = {
            "event": "updated",
            "data": {
                "id": 1,
                "url": "/api/dcim/devices/1/",
                "display": "router.example.net",
                "name": "router.example.net",
                "device_role": {
                    "id": 7,
                    "url": "/api/dcim/device-roles/7/",
                    "display": "Router",
                    "name": "Router",
                    "slug": "router",
                },
                "platform": {
                    "id": 3,
                    "url": "/api/dcim/platforms/3/",
                    "display": "Juniper Junos",
                    "name": "Juniper Junos",
                    "slug": "juniper-junos",
                },
                "status": {"value": "offline", "label": "Offline"},
                "local_context_data": None,
                "tags": [],
            },
        }
        response = self.client.post(url, **self.header, data=data, format="json")
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(Router.objects.get(netbox_device_id=1).status, "disabled")

        data = {
            "event": "deleted",
            "data": {
                "id": 1,
                "url": "/api/dcim/devices/1/",
                "display": "router.example.net",
                "name": "router.example.net",
                "device_role": {
                    "id": 7,
                    "url": "/api/dcim/device-roles/7/",
                    "display": "Router",
                    "name": "Router",
                    "slug": "router",
                },
                "platform": {
                    "id": 3,
                    "url": "/api/dcim/platforms/3/",
                    "display": "Juniper Junos",
                    "name": "Juniper Junos",
                    "slug": "juniper-junos",
                },
                "status": {"value": "offline", "label": "Offline"},
                "local_context_data": None,
                "tags": [],
            },
        }
        response = self.client.post(url, **self.header, data=data, format="json")
        self.assertHttpStatus(response, status.HTTP_200_OK)
        with self.assertRaises(Router.DoesNotExist):
            Router.objects.get(netbox_device_id=1)


class RoutingPolicyTest(APIViewTestCases.View):
    model = RoutingPolicy
    brief_fields = ["id", "url", "display", "name", "slug", "type"]
    create_data = [
        {
            "name": "Test1",
            "slug": "test1",
            "type": RoutingPolicyType.EXPORT,
            "weight": 1,
        },
        {
            "name": "Test2",
            "slug": "test2",
            "type": RoutingPolicyType.EXPORT,
            "weight": 2,
        },
        {
            "name": "Test3",
            "slug": "test3",
            "type": RoutingPolicyType.IMPORT_EXPORT,
            "weight": 3,
        },
    ]
    bulk_update_data = {"description": "Awesome routing policy"}

    @classmethod
    def setUpTestData(cls):
        RoutingPolicy.objects.bulk_create(
            [
                RoutingPolicy(
                    name="Example 1",
                    slug="example-1",
                    type=RoutingPolicyType.EXPORT,
                    weight=0,
                ),
                RoutingPolicy(
                    name="Example 2",
                    slug="example-2",
                    type=RoutingPolicyType.IMPORT,
                    weight=0,
                ),
                RoutingPolicy(
                    name="Example 3",
                    slug="example-3",
                    type=RoutingPolicyType.EXPORT,
                    weight=0,
                ),
            ]
        )
