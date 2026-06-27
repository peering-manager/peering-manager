from django.contrib.auth.models import AnonymousUser, User
from django.test import override_settings
from django.urls import reverse

from peering.models import AutonomousSystem
from peering.tables import AutonomousSystemTable
from utils.testing import TestCase

from ..models import TableConfig


class TableConfigResolutionTest(TestCase):
    def _columns(self, table):
        return [name for name, _ in table.selected_columns]

    def test_default_applies_without_user_preference(self):
        TableConfig.objects.create(
            table="AutonomousSystemTable", columns=["asn", "name"]
        )
        table = AutonomousSystemTable(AutonomousSystem.objects.none())
        self.assertEqual(["asn", "name"], self._columns(table))

    def test_default_applies_to_anonymous_user(self):
        TableConfig.objects.create(
            table="AutonomousSystemTable", columns=["asn", "name"]
        )
        table = AutonomousSystemTable(
            AutonomousSystem.objects.none(), user=AnonymousUser()
        )
        self.assertEqual(["asn", "name"], self._columns(table))

    @override_settings(
        DEFAULT_USER_PREFERENCES={
            "tables": {"AutonomousSystemTable": {"columns": ["asn", "irr_as_set"]}}
        }
    )
    def test_default_user_preferences_used_when_no_table_config(self):
        table = AutonomousSystemTable(
            AutonomousSystem.objects.none(), user=AnonymousUser()
        )
        self.assertEqual(["asn", "irr_as_set"], self._columns(table))

    def test_user_preference_overrides_default(self):
        TableConfig.objects.create(
            table="AutonomousSystemTable", columns=["asn", "name"]
        )
        self.user.preferences.refresh_from_db()
        self.user.preferences.set(
            "tables.AutonomousSystemTable.columns", ["asn", "irr_as_set"], commit=True
        )
        table = AutonomousSystemTable(AutonomousSystem.objects.none(), user=self.user)
        self.assertEqual(["asn", "irr_as_set"], self._columns(table))


class TableConfigModalTest(TestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("peering:autonomoussystem_list")

    def test_set_default_requires_permission(self):
        self.add_permissions("peering.view_autonomoussystem")

        self.client.post(self.url, data={"set_default": "", "columns": ["asn", "name"]})
        self.assertFalse(
            TableConfig.objects.filter(table="AutonomousSystemTable").exists()
        )

    def test_set_default_ignores_empty_columns(self):
        self.add_permissions(
            "peering.view_autonomoussystem", "extras.change_tableconfig"
        )

        self.client.post(self.url, data={"set_default": "", "columns": []})
        self.assertFalse(
            TableConfig.objects.filter(table="AutonomousSystemTable").exists()
        )

    def test_set_and_clear_default(self):
        self.add_permissions(
            "peering.view_autonomoussystem",
            "extras.change_tableconfig",
            "extras.delete_tableconfig",
        )

        self.client.post(self.url, data={"set_default": "", "columns": ["asn", "name"]})
        config = TableConfig.objects.get(table="AutonomousSystemTable")
        self.assertEqual(["asn", "name"], config.columns)
        self.assertEqual(AutonomousSystem, config.object_type.model_class())

        self.client.post(self.url, data={"clear_default": ""})
        self.assertFalse(
            TableConfig.objects.filter(table="AutonomousSystemTable").exists()
        )

    def test_reset_falls_back_to_default(self):
        self.add_permissions("peering.view_autonomoussystem")
        TableConfig.objects.create(
            table="AutonomousSystemTable", columns=["asn", "name"]
        )

        self.client.post(self.url, data={"save": "", "columns": ["asn"]})
        self.client.post(self.url, data={"reset": ""})

        fresh_user = User.objects.get(pk=self.user.pk)
        self.assertIsNone(
            fresh_user.preferences.get("tables.AutonomousSystemTable.columns")
        )
        table = AutonomousSystemTable(AutonomousSystem.objects.none(), user=fresh_user)
        self.assertEqual(["asn", "name"], [name for name, _ in table.selected_columns])
