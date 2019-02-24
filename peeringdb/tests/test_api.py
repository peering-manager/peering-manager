from django.urls import reverse
from django.utils import timezone

from peeringdb.models import Synchronization
from utils.testing import APITestCase


class CacheTest(APITestCase):
    def test_statistics(self):
        url = reverse("peeringdb-api:cache-statistics")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["network-count"], 0)
        self.assertEqual(response.data["network-ixlan-count"], 0)
        self.assertEqual(response.data["peer-record-count"], 0)

    # Increase testing time by a considerable amount of time
    # def test_update_local(self):
    #     url = reverse("peeringdb-api:cache-update-local")
    #     response = self.client.post(url, **self.header)
    #     self.assertIsNotNone(response.data["synchronization"])

    def test_clear_local(self):
        url = reverse("peeringdb-api:cache-clear-local")
        response = self.client.post(url, **self.header)
        self.assertEqual(response.data["status"], "success")

    def test_index_peer_records(self):
        url = reverse("peeringdb-api:cache-index-peer-records")
        response = self.client.post(url, **self.header)
        self.assertEqual(response.data["peer-record-count"], 0)


class SynchronizationTest(APITestCase):
    def setUp(self):
        super().setUp()

        for i in range(0, 10):
            Synchronization.objects.create(
                time=timezone.now(), added=i, updated=i, deleted=i
            )

    def test_get_synchronization(self):
        url = reverse("peeringdb-api:synchronization-detail", kwargs={"pk": 1})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["added"], 0)

    def test_list_synchronizations(self):
        url = reverse("peeringdb-api:synchronization-list")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["count"], 10)
