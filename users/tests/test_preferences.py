from django.contrib.auth.models import User
from django.test import override_settings
from django.test.client import RequestFactory
from django.urls import reverse

from peering.models import AutonomousSystem
from peering.tables import AutonomousSystemTable
from utils.testing import TestCase

DEFAULT_USER_PREFERENCES = {"pagination": {"per_page": 250}}


class UserPreferencesTest(TestCase):
    @override_settings(DEFAULT_USER_PREFERENCES=DEFAULT_USER_PREFERENCES)
    def test_default_preferences(self):
        user = User.objects.create(username="User 1")
        self.assertEqual(user.preferences.data, DEFAULT_USER_PREFERENCES)

    def test_table_ordering(self):
        url = reverse("peering:autonomoussystem_list")
        response = self.client.get(f"{url}?sort=asn")
        self.assertEqual(response.status_code, 200)

        # Check that table ordering preference has been recorded
        self.user.refresh_from_db()
        ordering = self.user.preferences.get("tables.AutonomousSystemTable.ordering")
        self.assertEqual(ordering, ["asn"])

        # Check that a recorded preference is honored by default
        self.user.preferences.set(
            "tables.AutonomousSystemTable.ordering", ["-asn"], commit=True
        )
        table = AutonomousSystemTable(AutonomousSystem.objects.all())
        request = RequestFactory().get(url)
        request.user = self.user
        table.configure(request)
        self.assertEqual(table.order_by, ("-asn",))
