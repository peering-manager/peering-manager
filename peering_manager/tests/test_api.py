from django.urls import reverse
from rest_framework import status

from peering.models import AutonomousSystem
from utils.testing import APITestCase


class AppTest(APITestCase):
    def test_root(self):
        url = reverse("api-root")
        response = self.client.get(f"{url}?format=api", **self.header)

        self.assertEqual(response.status_code, 200)

    def test_status(self):
        url = reverse("api-status")
        response = self.client.get(f"{url}?format=api", **self.header)

        self.assertEqual(response.status_code, 200)


class ListErrorTest(APITestCase):
    """
    A list endpoint reports the errors of a request as a list aligned with the entries of that
    request, one item per entry and empty for the entries that validated.
    """

    model = AutonomousSystem

    def test_errors_align_with_request_entries(self):
        url = self._get_list_url()

        for label, data, invalid_index in (
            ("trailing entry fails", [{"asn": 64541, "name": "Valid"}, {"name": "No ASN"}], 1),
            ("leading entry fails", [{"name": "No ASN"}, {"asn": 64542, "name": "Valid"}], 0),
        ):
            with self.subTest(label):
                response = self.client.post(url, data, format="json", **self.header)

                self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
                self.assertIsInstance(response.data, list)
                self.assertEqual(len(response.data), len(data))
                self.assertIn("asn", response.data[invalid_index])
                self.assertEqual(response.data[1 - invalid_index], {})

        self.assertFalse(AutonomousSystem.objects.exists())
