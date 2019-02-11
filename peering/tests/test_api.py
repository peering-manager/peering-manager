from django.urls import reverse

from rest_framework import status

from peering.constants import *
from peering.models import (
    AutonomousSystem,
    Community,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from utils.testing import APITestCase


class AutonomousSystemTest(APITestCase):
    def setUp(self):
        super().setUp()

        self.autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer"
        )

    def test_get_autonomous_system(self):
        url = reverse(
            "peering-api:autonomoussystem-detail",
            kwargs={"pk": self.autonomous_system.pk},
        )
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["asn"], self.autonomous_system.asn)

    def test_list_autonomous_systems(self):
        url = reverse("peering-api:autonomoussystem-list")
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["count"], 1)

    def test_create_autonomous_system(self):
        data = {"asn": 29467, "name": "LuxNetwork S.A."}

        url = reverse("peering-api:autonomoussystem-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(AutonomousSystem.objects.count(), 2)
        autonomous_system = AutonomousSystem.objects.get(pk=response.data["id"])
        self.assertEqual(autonomous_system.asn, data["asn"])

    def test_create_autonomous_system_bulk(self):
        data = [{"asn": 15169, "name": "Google"}, {"asn": 32934, "name": "Facebook"}]

        url = reverse("peering-api:autonomoussystem-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(AutonomousSystem.objects.count(), 3)
        self.assertEqual(response.data[0]["asn"], data[0]["asn"])
        self.assertEqual(response.data[1]["asn"], data[1]["asn"])

    def test_update_autonomous_system(self):
        data = {"asn": 201281, "name": "Guillaume Mazoyer"}

        url = reverse(
            "peering-api:autonomoussystem-detail",
            kwargs={"pk": self.autonomous_system.pk},
        )
        response = self.client.put(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(AutonomousSystem.objects.count(), 1)
        autonomous_system = AutonomousSystem.objects.get(pk=response.data["id"])
        self.assertEqual(autonomous_system.asn, data["asn"])

    def test_delete_autonomous_system(self):
        url = reverse(
            "peering-api:autonomoussystem-detail",
            kwargs={"pk": self.autonomous_system.pk},
        )
        response = self.client.delete(url, **self.header)

        self.assertStatus(response, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AutonomousSystem.objects.count(), 0)


class CommunityTest(APITestCase):
    def setUp(self):
        super().setUp()

        self.community = Community.objects.create(
            name="Test", value="64500:1", type=COMMUNITY_TYPE_EGRESS
        )

    def test_get_community(self):
        url = reverse("peering-api:community-detail", kwargs={"pk": self.community.pk})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["value"], self.community.value)

    def test_list_communities(self):
        url = reverse("peering-api:community-list")
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["count"], 1)

    def test_create_community(self):
        data = {"name": "Other", "value": "64500:2", "type": COMMUNITY_TYPE_EGRESS}

        url = reverse("peering-api:community-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(Community.objects.count(), 2)
        community = Community.objects.get(pk=response.data["id"])
        self.assertEqual(community.value, data["value"])

    def test_create_community_bulk(self):
        data = [
            {"name": "Test1", "value": "64500:11", "type": COMMUNITY_TYPE_EGRESS},
            {"name": "Test2", "value": "64500:12", "type": COMMUNITY_TYPE_EGRESS},
        ]

        url = reverse("peering-api:community-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(Community.objects.count(), 3)
        self.assertEqual(response.data[0]["value"], data[0]["value"])
        self.assertEqual(response.data[1]["value"], data[1]["value"])

    def test_update_community(self):
        data = {"name": "Other", "value": "64500:2", "type": COMMUNITY_TYPE_INGRESS}

        url = reverse("peering-api:community-detail", kwargs={"pk": self.community.pk})
        response = self.client.put(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(Community.objects.count(), 1)
        community = Community.objects.get(pk=response.data["id"])
        self.assertEqual(community.value, data["value"])

    def test_delete_community(self):
        url = reverse("peering-api:community-detail", kwargs={"pk": self.community.pk})
        response = self.client.delete(url, **self.header)

        self.assertStatus(response, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Community.objects.count(), 0)


class InternetExchangeTest(APITestCase):
    def setUp(self):
        super().setUp()

        self.internet_exchange = InternetExchange.objects.create(
            name="Test", slug="test"
        )

    def test_get_internet_exchange(self):
        url = reverse(
            "peering-api:internetexchange-detail",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["slug"], self.internet_exchange.slug)

    def test_list_internet_exchanges(self):
        url = reverse("peering-api:internetexchange-list")
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["count"], 1)

    def test_create_internet_exchange(self):
        data = {"name": "Other", "slug": "other"}

        url = reverse("peering-api:internetexchange-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(InternetExchange.objects.count(), 2)
        internet_exchange = InternetExchange.objects.get(pk=response.data["id"])
        self.assertEqual(internet_exchange.slug, data["slug"])

    def test_create_internet_exchange_bulk(self):
        data = [{"name": "Test1", "slug": "test1"}, {"name": "Test2", "slug": "test2"}]

        url = reverse("peering-api:internetexchange-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(InternetExchange.objects.count(), 3)
        self.assertEqual(response.data[0]["slug"], data[0]["slug"])
        self.assertEqual(response.data[1]["slug"], data[1]["slug"])

    def test_update_internet_exchange(self):
        data = {"name": "Test", "slug": "test"}

        url = reverse(
            "peering-api:internetexchange-detail",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.put(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(InternetExchange.objects.count(), 1)
        internet_exchange = InternetExchange.objects.get(pk=response.data["id"])
        self.assertEqual(internet_exchange.slug, data["slug"])

    def test_delete_internet_exchange(self):
        url = reverse(
            "peering-api:internetexchange-detail",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.delete(url, **self.header)

        self.assertStatus(response, status.HTTP_204_NO_CONTENT)
        self.assertEqual(InternetExchange.objects.count(), 0)


class InternetExchangePeeringSessionTest(APITestCase):
    def setUp(self):
        super().setUp()

        self.autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer"
        )
        self.internet_exchange = InternetExchange.objects.create(
            name="Test", slug="test"
        )
        self.internet_exchange_peering_session = InternetExchangePeeringSession.objects.create(
            autonomous_system=self.autonomous_system,
            internet_exchange=self.internet_exchange,
            ip_address="2001:db8::1",
        )

    def test_get_internet_exchange_peering_session(self):
        url = reverse(
            "peering-api:internetexchangepeeringsession-detail",
            kwargs={"pk": self.internet_exchange_peering_session.pk},
        )
        response = self.client.get(url, **self.header)

        self.assertEqual(
            response.data["ip_address"],
            self.internet_exchange_peering_session.ip_address,
        )

    def test_list_internet_exchange_peering_sessions(self):
        url = reverse("peering-api:internetexchangepeeringsession-list")
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["count"], 1)

    def test_create_internet_exchange_peering_session(self):
        data = {
            "autonomous_system": self.autonomous_system.pk,
            "internet_exchange": self.internet_exchange.pk,
            "ip_address": "192.168.0.1",
        }

        url = reverse("peering-api:internetexchangepeeringsession-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(InternetExchangePeeringSession.objects.count(), 2)
        internet_exchange_peering_session = InternetExchangePeeringSession.objects.get(
            pk=response.data["id"]
        )
        self.assertEqual(
            internet_exchange_peering_session.ip_address, data["ip_address"]
        )

    def test_create_internet_exchange_peering_session_bulk(self):
        data = [
            {
                "autonomous_system": self.autonomous_system.pk,
                "internet_exchange": self.internet_exchange.pk,
                "ip_address": "10.0.0.1",
            },
            {
                "autonomous_system": self.autonomous_system.pk,
                "internet_exchange": self.internet_exchange.pk,
                "ip_address": "10.0.0.2",
            },
        ]

        url = reverse("peering-api:internetexchangepeeringsession-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(InternetExchangePeeringSession.objects.count(), 3)
        self.assertEqual(response.data[0]["ip_address"], data[0]["ip_address"])
        self.assertEqual(response.data[1]["ip_address"], data[1]["ip_address"])

    def test_update_internet_exchange_peering_session(self):
        data = {
            "autonomous_system": self.autonomous_system.pk,
            "internet_exchange": self.internet_exchange.pk,
            "ip_address": "2001:db8::2",
        }

        url = reverse(
            "peering-api:internetexchangepeeringsession-detail",
            kwargs={"pk": self.internet_exchange_peering_session.pk},
        )
        response = self.client.put(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(InternetExchangePeeringSession.objects.count(), 1)
        internet_exchange_peering_session = InternetExchangePeeringSession.objects.get(
            pk=response.data["id"]
        )
        self.assertEqual(
            internet_exchange_peering_session.ip_address, data["ip_address"]
        )

    def test_delete_internet_exchange_peering_session(self):
        url = reverse(
            "peering-api:internetexchangepeeringsession-detail",
            kwargs={"pk": self.internet_exchange_peering_session.pk},
        )
        response = self.client.delete(url, **self.header)

        self.assertStatus(response, status.HTTP_204_NO_CONTENT)
        self.assertEqual(InternetExchangePeeringSession.objects.count(), 0)


class RouterTest(APITestCase):
    def setUp(self):
        super().setUp()

        self.router = Router.objects.create(
            name="Test", hostname="test.example.com", platform=PLATFORM_JUNOS
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
            "platform": PLATFORM_JUNOS,
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
                "platform": PLATFORM_JUNOS,
            },
            {
                "name": "Test2",
                "hostname": "test2.example.com",
                "platform": PLATFORM_JUNOS,
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
            "platform": PLATFORM_IOSXR,
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


class RoutingPolicyTest(APITestCase):
    def setUp(self):
        super().setUp()

        self.routing_policy = RoutingPolicy.objects.create(
            name="Test", slug="test", type=ROUTING_POLICY_TYPE_EXPORT
        )

    def test_get_routing_policy(self):
        url = reverse(
            "peering-api:routingpolicy-detail", kwargs={"pk": self.routing_policy.pk}
        )
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["slug"], self.routing_policy.slug)

    def test_list_routing_policies(self):
        url = reverse("peering-api:routingpolicy-list")
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["count"], 1)

    def test_create_routing_policy(self):
        data = {"name": "Other", "slug": "other", "type": ROUTING_POLICY_TYPE_EXPORT}

        url = reverse("peering-api:routingpolicy-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(RoutingPolicy.objects.count(), 2)
        routing_policy = RoutingPolicy.objects.get(pk=response.data["id"])
        self.assertEqual(routing_policy.slug, data["slug"])

    def test_create_routing_policy_bulk(self):
        data = [
            {"name": "Test1", "slug": "test1", "type": ROUTING_POLICY_TYPE_EXPORT},
            {"name": "Test2", "slug": "test2", "type": ROUTING_POLICY_TYPE_EXPORT},
        ]

        url = reverse("peering-api:routingpolicy-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(RoutingPolicy.objects.count(), 3)
        self.assertEqual(response.data[0]["slug"], data[0]["slug"])
        self.assertEqual(response.data[1]["slug"], data[1]["slug"])

    def test_update_router(self):
        data = {"name": "Test", "slug": "test", "type": ROUTING_POLICY_TYPE_IMPORT}

        url = reverse(
            "peering-api:routingpolicy-detail", kwargs={"pk": self.routing_policy.pk}
        )
        response = self.client.put(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(RoutingPolicy.objects.count(), 1)
        routing_policy = RoutingPolicy.objects.get(pk=response.data["id"])
        self.assertEqual(routing_policy.type, data["type"])

    def test_delete_routing_policy(self):
        url = reverse(
            "peering-api:routingpolicy-detail", kwargs={"pk": self.routing_policy.pk}
        )
        response = self.client.delete(url, **self.header)

        self.assertStatus(response, status.HTTP_204_NO_CONTENT)
        self.assertEqual(RoutingPolicy.objects.count(), 0)
