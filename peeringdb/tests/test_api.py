from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from utils.testing import APITestCase

from ..models import *
from ..sync import NAMESPACES


class CacheTest(APITestCase):
    def test_statistics(self):
        url = reverse("peeringdb-api:cache-statistics")
        response = self.client.get(url, **self.header)
        for namespace in [*list(NAMESPACES.keys()), "sync"]:
            self.assertEqual(response.data[f"{namespace}-count"], 0)

    def test_update_local(self):
        url = reverse("peeringdb-api:cache-update-local")
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)

    def test_clear_local(self):
        url = reverse("peeringdb-api:cache-clear-local")
        response = self.client.post(url, **self.header)
        self.assertEqual(response.data["status"], "success")


class SynchronisationTest(APITestCase):
    def setUp(self):
        super().setUp()

        for i in range(1, 10):
            Synchronisation.objects.create(
                time=timezone.now(), created=i, updated=i, deleted=i
            )

    def test_get_synchronisation(self):
        url = reverse("peeringdb-api:synchronisation-detail", kwargs={"pk": 1})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["created"], 1)

    def test_list_synchronisations(self):
        url = reverse("peeringdb-api:synchronisation-list")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["count"], 9)
