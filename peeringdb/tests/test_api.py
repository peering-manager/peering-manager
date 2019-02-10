from django.urls import reverse
from django.utils import timezone

from rest_framework import status

from peeringdb.models import Synchronization
from utils.testing import APITestCase


class SynchronizationTest(APITestCase):
    def setUp(self):
        super().setUp()

        for i in range(0, 10):
            Synchronization.objects.create(
                time=timezone.now(), added=i, updated=i, deleted=i
            )

    def test_get_synchornization(self):
        url = reverse("peeringdb-api:synchronization-detail", kwargs={"pk": 1})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["added"], 0)

    def test_list_synchornizations(self):
        url = reverse("peeringdb-api:synchronization-list")
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["count"], 10)
