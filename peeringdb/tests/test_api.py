from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from peeringdb.models import Synchronization
from utils.testing import APITestCase

from .test_http import mocked_synchronization


class CacheTest(APITestCase):
    def test_statistics(self):
        url = reverse("peeringdb-api:cache-statistics")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["contact-count"], 0)
        self.assertEqual(response.data["network-count"], 0)
        self.assertEqual(response.data["network-ixlan-count"], 0)
        self.assertEqual(response.data["peer-record-count"], 0)

    @patch("peeringdb.http.requests.get", side_effect=mocked_synchronization)
    def test_update_local(self, *_):
        url = reverse("peeringdb-api:cache-update-local")
        response = self.client.post(url, **self.header)
        self.assertIsNotNone(response.data["synchronization"])
        self.assertEqual(8, response.data["synchronization"]["added"])

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

        for i in range(1, 10):
            Synchronization.objects.create(
                time=timezone.now(), added=i, updated=i, deleted=i
            )

    def test_get_synchronization(self):
        url = reverse("peeringdb-api:synchronization-detail", kwargs={"pk": 10})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["added"], 9)

    def test_list_synchronizations(self):
        url = reverse("peeringdb-api:synchronization-list")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["count"], 9)
