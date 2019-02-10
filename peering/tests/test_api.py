from django.urls import reverse

from rest_framework import status

from peering.models import AutonomousSystem, InternetExchange
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

    def test_list_gameservers(self):
        url = reverse("peering-api:autonomoussystem-list")
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["count"], 1)

    def test_create_gameserver(self):
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

    def test_list_gameservers(self):
        url = reverse("peering-api:internetexchange-list")
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["count"], 1)

    def test_create_gameserver(self):
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
