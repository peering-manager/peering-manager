from django.urls import reverse

from utils.tests import ViewTestCase


class PeeringManagerViewsTestCase(ViewTestCase):
    def test_homepage_view(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_error500_view(self):
        with self.assertRaises(Exception):
            self.client.get("/error500/")
