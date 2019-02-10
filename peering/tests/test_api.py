from django.urls import reverse

from rest_framework import status

from peering.models import AutonomousSystem
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
