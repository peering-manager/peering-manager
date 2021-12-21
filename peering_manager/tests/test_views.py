import urllib.parse

from django.test import override_settings
from django.urls import reverse

from utils.tests import ViewTestCase


class PeeringManagerViewsTestCase(ViewTestCase):
    @override_settings(LOGIN_REQUIRED=False)
    def test_homepage_view(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    @override_settings(LOGIN_REQUIRED=False)
    def test_search(self):
        response = self.client.get(f"{reverse('search')}?q=foo")
        self.assertHttpStatus(response, 200)

    @override_settings(LOGIN_REQUIRED=False)
    def test_error500_view(self):
        with self.assertRaises(Exception):
            self.client.get("/error500/")
