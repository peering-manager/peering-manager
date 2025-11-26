from unittest.mock import patch

from django.urls import reverse
from rest_framework import status

from bgp.models import Relationship
from net.models import Connection
from utils.testing import APITestCase, APIViewTestCases

from ..constants import *
from ..enums import *
from ..models import *
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
        "display_url",
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
        with patch(
            "peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen
        ):
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
        # To avoid side effects in other tests
        self.user.preferences.delete("context")


class BGPGroupTest(APIViewTestCases.View):
    model = BGPGroup
    brief_fields = ["id", "url", "display_url", "display", "name", "slug", "status"]
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


class DirectPeeringSessionTest(APIViewTestCases.View):
    model = DirectPeeringSession
    brief_fields = ["id", "url", "display_url", "display", "ip_address", "status"]
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
        connection = Connection.objects.create(vlan=2000)
        routing_policy = RoutingPolicy.objects.create(
            name="Import", slug="import", type=RoutingPolicyType.IMPORT, weight=0
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
                    connection=connection,
                ),
            ]
        )
        cls.create_data = [
            {
                "service_reference": "PNI-0001",
                "local_autonomous_system": local_autonomous_system.pk,
                "autonomous_system": autonomous_system.pk,
                "relationship": relationship_private_peering.pk,
                "ip_address": "192.0.2.1/32",
            },
            {
                "local_autonomous_system": local_autonomous_system.pk,
                "autonomous_system": autonomous_system.pk,
                "relationship": relationship_private_peering.pk,
                "ip_address": "192.0.2.2/32",
            },
            {
                "local_autonomous_system": local_autonomous_system.pk,
                "autonomous_system": autonomous_system.pk,
                "relationship": relationship_private_peering.pk,
                "ip_address": "192.0.2.3/32",
                "connection": connection.pk,
                "import_routing_policies": [routing_policy.pk],
            },
        ]


class InternetExchangeTest(APIViewTestCases.View):
    model = InternetExchange
    brief_fields = ["id", "url", "display_url", "display", "name", "slug", "status"]
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
    brief_fields = [
        "id",
        "url",
        "display_url",
        "display",
        "ip_address",
        "status",
        "is_route_server",
    ]
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


class RoutingPolicyTest(APIViewTestCases.View):
    model = RoutingPolicy
    brief_fields = ["id", "url", "display_url", "display", "name", "slug", "type"]
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
