from django.urls import reverse
from rest_framework import status
from unittest.mock import patch

from peering.constants import *
from peering.enums import BGPRelationship, CommunityType, Platform, RoutingPolicyType
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
from peering.tests.mocked_data import *
from utils.testing import APITestCase, StandardAPITestCases


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("peering-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class StaticChoiceTest(APITestCase):
    def test_get_static_choice(self):
        url = reverse(
            "peering-api:field-choice-detail", kwargs={"pk": "router:platform"}
        )
        response = self.client.get(url, **self.header)
        self.assertEqual(len(response.data), len(Platform.choices))

    def test_list_static_choices(self):
        url = reverse("peering-api:field-choice-list")
        response = self.client.get(url, **self.header)
        self.assertEqual(len(response.data), 6)


class AutonomousSystemTest(StandardAPITestCases.View):
    model = AutonomousSystem
    brief_fields = [
        "id",
        "url",
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

    @classmethod
    def setUpTestData(cls):
        cls.autonomous_system = AutonomousSystem.objects.create(
            asn=65536, name="Test", irr_as_set="AS-MOCKED"
        )

    def test_create_autonomous_system_with_nested(self):
        routing_policy = RoutingPolicy.objects.create(
            name="Test", slug="test", type=RoutingPolicyType.IMPORT_EXPORT, weight=0
        )
        data = {
            "asn": 201281,
            "name": "Guillaume Mazoyer",
            "import_routing_policies": [routing_policy.pk],
            "export_routing_policies": [routing_policy.pk],
            "affiliated": True,
        }

        url = reverse("peering-api:autonomoussystem-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(AutonomousSystem.objects.count(), 2)
        autonomous_system = AutonomousSystem.objects.get(pk=response.data["id"])
        self.assertEqual(autonomous_system.asn, data["asn"])

    def test_update_autonomous_system_with_nested(self):
        routing_policy = RoutingPolicy.objects.create(
            name="Test", slug="test", type=RoutingPolicyType.IMPORT_EXPORT, weight=0
        )
        data = {
            "asn": 65536,
            "name": "Guillaume Mazoyer",
            "import_routing_policies": [routing_policy.pk],
            "export_routing_policies": [routing_policy.pk],
        }

        url = reverse(
            "peering-api:autonomoussystem-detail",
            kwargs={"pk": self.autonomous_system.pk},
        )
        response = self.client.put(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(AutonomousSystem.objects.count(), 1)
        autonomous_system = AutonomousSystem.objects.get(pk=response.data["id"])
        self.assertEqual(autonomous_system.asn, data["asn"])

    def test_synchronize_with_peeringdb(self):
        autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Test", irr_as_set="AS-TEST"
        )
        url = reverse(
            "peering-api:autonomoussystem-synchronize-with-peeringdb",
            kwargs={"pk": autonomous_system.pk},
        )
        response = self.client.post(url, format="json", **self.header)
        self.assertStatus(response, status.HTTP_200_OK)

    def test_get_irr_as_set_prefixes(self):
        with patch("peering.subprocess.Popen", side_effect=mocked_subprocess_popen):
            url = reverse(
                "peering-api:autonomoussystem-get-irr-as-set-prefixes",
                kwargs={"pk": self.autonomous_system.pk},
            )
            response = self.client.get(url, format="json", **self.header)
            self.assertStatus(response, status.HTTP_200_OK)
            self.assertEqual(len(response.data["prefixes"]["ipv6"]), 1)
            self.assertEqual(len(response.data["prefixes"]["ipv4"]), 1)

    def test_common_internet_exchanges(self):
        local_as = AutonomousSystem.objects.create(
            asn=65535, name="Local", irr_as_set="AS-LOCAL", affiliated=True
        )
        self.user.preferences.set("context.asn", local_as.pk, commit=True)
        url = reverse(
            "peering-api:autonomoussystem-common-internet-exchanges",
            kwargs={"pk": self.autonomous_system.pk},
        )
        response = self.client.get(url, format="json", **self.header)
        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data["common-internet-exchanges"], [])

    def test_find_potential_ix_peering_sessions(self):
        local_as = AutonomousSystem.objects.create(
            asn=65535, name="Local", irr_as_set="AS-LOCAL", affiliated=True
        )
        self.user.preferences.set("context.asn", local_as.pk, commit=True)
        url = reverse(
            "peering-api:autonomoussystem-find-potential-ix-peering-sessions",
            kwargs={"pk": self.autonomous_system.pk},
        )
        response = self.client.patch(url, format="json", **self.header)
        self.assertStatus(response, status.HTTP_200_OK)


class BGPGroupTest(StandardAPITestCases.View):
    model = BGPGroup
    brief_fields = ["id", "url", "name", "slug"]
    create_data = [
        {"name": "Test 1", "slug": "test-1"},
        {"name": "Test 2", "slug": "test-2"},
        {"name": "Test 3", "slug": "test-3"},
    ]

    @classmethod
    def setUpTestData(cls):
        cls.bgp_group = BGPGroup.objects.create(name="Test", slug="test")

    def test_create_bgp_group_with_nested(self):
        routing_policy = RoutingPolicy.objects.create(
            name="Test", slug="test", type=RoutingPolicyType.IMPORT_EXPORT, weight=0
        )
        community = Community.objects.create(
            name="Test", slug="test", value="64500:1", type=CommunityType.EGRESS
        )
        data = {
            "name": "Other",
            "slug": "other",
            "import_routing_policies": [routing_policy.pk],
            "export_routing_policies": [routing_policy.pk],
            "communities": [community.pk],
        }

        url = reverse("peering-api:bgpgroup-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(BGPGroup.objects.count(), 2)
        bgp_group = BGPGroup.objects.get(pk=response.data["id"])
        self.assertEqual(bgp_group.slug, data["slug"])

    def test_update_bgp_group_with_nested(self):
        routing_policy = RoutingPolicy.objects.create(
            name="Test", slug="test", type=RoutingPolicyType.IMPORT_EXPORT, weight=0
        )
        community = Community.objects.create(
            name="Test", slug="test", value="64500:1", type=CommunityType.EGRESS
        )
        data = {
            "name": "Changed",
            "slug": "test",
            "import_routing_policies": [routing_policy.pk],
            "export_routing_policies": [routing_policy.pk],
            "communities": [community.pk],
        }

        url = reverse("peering-api:bgpgroup-detail", kwargs={"pk": self.bgp_group.pk})
        response = self.client.put(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(BGPGroup.objects.count(), 1)
        bgp_group = BGPGroup.objects.get(pk=response.data["id"])
        self.assertEqual(bgp_group.name, data["name"])

    def test_poll_peering_sessions(self):
        url = reverse(
            "peering-api:bgpgroup-poll-peering-sessions",
            kwargs={"pk": self.bgp_group.pk},
        )
        response = self.client.post(url, **self.header)
        self.assertStatus(response, status.HTTP_503_SERVICE_UNAVAILABLE)


class CommunityTest(StandardAPITestCases.View):
    model = Community
    brief_fields = ["id", "url", "name", "slug", "value", "type"]
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

    @classmethod
    def setUpTestData(cls):
        Community.objects.create(
            name="Test", slug="test", value="64500:1", type=CommunityType.EGRESS
        )


class ConfigurationTest(StandardAPITestCases.View):
    model = Configuration
    brief_fields = ["id", "url", "name"]
    create_data = [
        {"name": "Test1", "template": "test1_template"},
        {"name": "Test2", "template": "test2_template"},
        {"name": "Test3", "template": "test3_template"},
    ]

    @classmethod
    def setUpTestData(cls):
        Configuration.objects.create(name="Test", template="test_template")


class DirectPeeringSessionTest(StandardAPITestCases.View):
    model = DirectPeeringSession
    brief_fields = ["id", "ip_address", "enabled"]

    @classmethod
    def setUpTestData(cls):
        local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        autonomous_system = AutonomousSystem.objects.create(asn=64500, name="Dummy")
        cls.direct_peering_session = DirectPeeringSession.objects.create(
            local_autonomous_system=local_autonomous_system,
            autonomous_system=autonomous_system,
            relationship=BGPRelationship.PRIVATE_PEERING,
            ip_address="2001:db8::1",
            password="mypassword",
        )
        cls.create_data = [
            {
                "local_autonomous_system": local_autonomous_system.pk,
                "autonomous_system": autonomous_system.pk,
                "relationship": BGPRelationship.PRIVATE_PEERING,
                "ip_address": "198.51.100.1",
            },
            {
                "local_autonomous_system": local_autonomous_system.pk,
                "autonomous_system": autonomous_system.pk,
                "relationship": BGPRelationship.PRIVATE_PEERING,
                "ip_address": "198.51.100.2",
            },
            {
                "local_autonomous_system": local_autonomous_system.pk,
                "autonomous_system": autonomous_system.pk,
                "relationship": BGPRelationship.PRIVATE_PEERING,
                "ip_address": "198.51.100.3",
            },
        ]

    def test_encrypt_password(self):
        url = reverse(
            "peering-api:directpeeringsession-encrypt-password",
            kwargs={"pk": self.direct_peering_session.pk},
        )
        response = self.client.post(
            url, {"platform": Platform.JUNOS}, format="json", **self.header
        )

        self.assertIsNotNone(response.data["encrypted_password"])
        self.assertNotEqual(response.data["encrypted_password"], "")


class EmailTest(StandardAPITestCases.View):
    model = Email
    brief_fields = ["id", "url", "name"]
    create_data = [
        {"name": "Test1", "subject": "test1_subject", "template": "test1_template"},
        {"name": "Test2", "subject": "test2_subject", "template": "test2_template"},
        {"name": "Test3", "subject": "test3_subject", "template": "test3_template"},
    ]

    @classmethod
    def setUpTestData(cls):
        Email.objects.create(
            name="Test", subject="test_subject", template="test_template"
        )


class InternetExchangeTest(StandardAPITestCases.View):
    model = InternetExchange
    brief_fields = ["id", "url", "name", "slug"]

    @classmethod
    def setUpTestData(cls):
        cls.local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        cls.internet_exchange = InternetExchange.objects.create(
            name="Test",
            slug="test",
            local_autonomous_system=cls.local_autonomous_system,
        )
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

    def test_create_internet_exchange_with_nested(self):
        routing_policy = RoutingPolicy.objects.create(
            name="Test", slug="test", type=RoutingPolicyType.IMPORT_EXPORT, weight=0
        )
        community = Community.objects.create(
            name="Test", slug="test", value="64500:1", type=CommunityType.EGRESS
        )
        router = Router.objects.create(
            name="Test", hostname="test.example.com", platform=Platform.JUNOS
        )
        data = {
            "name": "Other",
            "slug": "other",
            "local_autonomous_system": self.local_autonomous_system.pk,
            "import_routing_policies": [routing_policy.pk],
            "export_routing_policies": [routing_policy.pk],
            "communities": [community.pk],
            "router": router.pk,
        }

        url = reverse("peering-api:internetexchange-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(InternetExchange.objects.count(), 2)
        internet_exchange = InternetExchange.objects.get(pk=response.data["id"])
        self.assertEqual(internet_exchange.slug, data["slug"])

    def test_update_internet_exchange_with_nested(self):
        routing_policy = RoutingPolicy.objects.create(
            name="Test", slug="test", type=RoutingPolicyType.IMPORT_EXPORT, weight=0
        )
        community = Community.objects.create(
            name="Test", slug="test", value="64500:1", type=CommunityType.EGRESS
        )
        router = Router.objects.create(
            name="Test", hostname="test.example.com", platform=Platform.JUNOS
        )
        data = {
            "name": "Test",
            "slug": "test",
            "local_autonomous_system": self.local_autonomous_system.pk,
            "import_routing_policies": [routing_policy.pk],
            "export_routing_policies": [routing_policy.pk],
            "communities": [community.pk],
            "router": router.pk,
        }

        url = reverse(
            "peering-api:internetexchange-detail",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.put(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(InternetExchange.objects.count(), 1)
        internet_exchange = InternetExchange.objects.get(pk=response.data["id"])
        self.assertEqual(internet_exchange.slug, data["slug"])

    def test_available_peers(self):
        url = reverse(
            "peering-api:internetexchange-available-peers",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.get(url, **self.header)
        self.assertStatus(response, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_import_peering_sessions(self):
        url = reverse(
            "peering-api:internetexchange-import-peering-sessions",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.post(url, **self.header)
        self.assertStatus(response, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_prefixes(self):
        url = reverse(
            "peering-api:internetexchange-prefixes",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.get(url, **self.header)

        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data["prefixes"], [])

    def test_configure_router(self):
        url = reverse(
            "peering-api:internetexchange-configure-router",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.get(url, **self.header)
        self.assertStatus(response, status.HTTP_503_SERVICE_UNAVAILABLE)
        response = self.client.post(url, **self.header)
        self.assertStatus(response, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_poll_peering_sessions(self):
        url = reverse(
            "peering-api:internetexchange-poll-peering-sessions",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.post(url, **self.header)
        self.assertStatus(response, status.HTTP_503_SERVICE_UNAVAILABLE)


class InternetExchangePeeringSessionTest(StandardAPITestCases.View):
    model = InternetExchangePeeringSession
    brief_fields = [
        "id",
        "ip_address",
        "enabled",
        "is_route_server",
    ]

    @classmethod
    def setUpTestData(cls):
        local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        autonomous_system = AutonomousSystem.objects.create(asn=64500, name="Dummy")
        internet_exchange = InternetExchange.objects.create(
            name="Test", slug="test", local_autonomous_system=local_autonomous_system
        )
        cls.internet_exchange_peering_session = (
            InternetExchangePeeringSession.objects.create(
                autonomous_system=autonomous_system,
                internet_exchange=internet_exchange,
                ip_address="2001:db8::1",
                password="mypassword",
            )
        )
        cls.create_data = [
            {
                "autonomous_system": autonomous_system.pk,
                "internet_exchange": internet_exchange.pk,
                "ip_address": "198.51.100.1",
            },
            {
                "autonomous_system": autonomous_system.pk,
                "internet_exchange": internet_exchange.pk,
                "ip_address": "198.51.100.2",
            },
            {
                "autonomous_system": autonomous_system.pk,
                "internet_exchange": internet_exchange.pk,
                "ip_address": "198.51.100.3",
            },
        ]

    def test_encrypt_password(self):
        url = reverse(
            "peering-api:internetexchangepeeringsession-encrypt-password",
            kwargs={"pk": self.internet_exchange_peering_session.pk},
        )
        response = self.client.post(
            url, {"platform": Platform.JUNOS}, format="json", **self.header
        )
        self.assertIsNotNone(response.data["encrypted_password"])
        self.assertNotEqual(response.data["encrypted_password"], "")


class RouterTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        cls.template = Configuration.objects.create(
            name="Test", template="Nothing useful"
        )
        cls.router = Router.objects.create(
            name="Test",
            hostname="test.example.com",
            platform=Platform.JUNOS,
            configuration_template=cls.template,
            local_autonomous_system=cls.local_autonomous_system,
        )

    def test_get_router(self):
        url = reverse("peering-api:router-detail", kwargs={"pk": self.router.pk})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["hostname"], self.router.hostname)

    def test_list_routers(self):
        url = reverse("peering-api:router-list")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["count"], 1)

    def test_create_router(self):
        data = {
            "name": "Other",
            "hostname": "other.example.com",
            "platform": Platform.JUNOS,
            "local_autonomous_system": self.local_autonomous_system.pk,
        }

        url = reverse("peering-api:router-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(Router.objects.count(), 2)
        router = Router.objects.get(pk=response.data["id"])
        self.assertEqual(router.hostname, data["hostname"])

    def test_create_router_with_nested(self):
        data = {
            "name": "Other",
            "hostname": "other.example.com",
            "platform": Platform.JUNOS,
            "configuration_template": self.template.pk,
            "local_autonomous_system": self.local_autonomous_system.pk,
        }

        url = reverse("peering-api:router-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(Router.objects.count(), 2)
        router = Router.objects.get(pk=response.data["id"])
        self.assertEqual(router.hostname, data["hostname"])

    def test_create_router_bulk(self):
        data = [
            {
                "name": "Test1",
                "hostname": "test1.example.com",
                "platform": Platform.JUNOS,
                "local_autonomous_system": self.local_autonomous_system.pk,
            },
            {
                "name": "Test2",
                "hostname": "test2.example.com",
                "platform": Platform.JUNOS,
                "local_autonomous_system": self.local_autonomous_system.pk,
            },
        ]

        url = reverse("peering-api:router-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(Router.objects.count(), 3)
        self.assertEqual(response.data[0]["hostname"], data[0]["hostname"])
        self.assertEqual(response.data[1]["hostname"], data[1]["hostname"])

    def test_update_router(self):
        data = {
            "name": "Test",
            "hostname": "test.example.com",
            "platform": Platform.IOSXR,
            "local_autonomous_system": self.local_autonomous_system.pk,
        }

        url = reverse("peering-api:router-detail", kwargs={"pk": self.router.pk})
        response = self.client.put(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(Router.objects.count(), 1)
        router = Router.objects.get(pk=response.data["id"])
        self.assertEqual(router.hostname, data["hostname"])

    def test_update_router_with_nested(self):
        data = {
            "name": "Test",
            "hostname": "test.example.com",
            "platform": Platform.IOSXR,
            "configuration_template": self.template.pk,
            "local_autonomous_system": self.local_autonomous_system.pk,
        }

        url = reverse("peering-api:router-detail", kwargs={"pk": self.router.pk})
        response = self.client.put(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(Router.objects.count(), 1)
        router = Router.objects.get(pk=response.data["id"])
        self.assertEqual(router.hostname, data["hostname"])

    def test_delete_router(self):
        url = reverse("peering-api:router-detail", kwargs={"pk": self.router.pk})
        response = self.client.delete(url, **self.header)

        self.assertStatus(response, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Router.objects.count(), 0)

    def test_configuration(self):
        url = reverse("peering-api:router-configuration", kwargs={"pk": self.router.pk})
        response = self.client.get(url, **self.header)
        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual("Nothing useful", response.data["configuration"])

    def test_test_napalm_connection(self):
        url = reverse(
            "peering-api:router-test-napalm-connection", kwargs={"pk": self.router.pk}
        )
        response = self.client.get(url, **self.header)
        self.assertStatus(response, status.HTTP_503_SERVICE_UNAVAILABLE)


class RoutingPolicyTest(StandardAPITestCases.View):
    model = RoutingPolicy
    brief_fields = ["id", "url", "name", "slug", "type"]
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

    @classmethod
    def setUpTestData(cls):
        RoutingPolicy.objects.create(
            name="Test", slug="test", type=RoutingPolicyType.EXPORT, weight=0
        )
