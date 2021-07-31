from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from peeringdb.models import Synchronization
from utils.testing import APITestCase


class CacheTest(APITestCase):
    def test_statistics(self):
        url = reverse("peeringdb-api:cache-statistics")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["fac-count"], 0)
        self.assertEqual(response.data["ix-count"], 0)
        self.assertEqual(response.data["ixfac-count"], 0)
        self.assertEqual(response.data["ixlan-count"], 0)
        self.assertEqual(response.data["ixlanpfx-count"], 0)
        self.assertEqual(response.data["net-count"], 0)
        self.assertEqual(response.data["poc-count"], 0)
        self.assertEqual(response.data["netfac-count"], 0)
        self.assertEqual(response.data["netixlan-count"], 0)
        self.assertEqual(response.data["org-count"], 0)
        self.assertEqual(response.data["sync-count"], 0)

    def test_update_local(self):
        url = reverse("peeringdb-api:cache-update-local")
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)

    def test_clear_local(self):
        url = reverse("peeringdb-api:cache-clear-local")
        response = self.client.post(url, **self.header)
        self.assertEqual(response.data["status"], "success")


class SynchronizationTest(APITestCase):
    def setUp(self):
        super().setUp()

        for i in range(1, 10):
            Synchronization.objects.create(
                time=timezone.now(), created=i, updated=i, deleted=i
            )

    def test_get_synchronization(self):
        url = reverse("peeringdb-api:synchronization-detail", kwargs={"pk": 1})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["created"], 1)

    def test_list_synchronizations(self):
        url = reverse("peeringdb-api:synchronization-list")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["count"], 9)
