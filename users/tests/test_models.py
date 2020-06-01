from django.contrib.auth.models import User
from django.test import TestCase

from users.models import UserPreferences


class UserPreferencesTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="testuser")
        user.preferences.data = {
            "a": True,
            "b": {"test": 1, "foo": 2},
            "c": {"test": {"x": 10}, "foo": {"y": 11}, "bar": {"z": 12}},
        }
        user.preferences.save()
        self.preferences = user.preferences

    def test_all(self):
        flattened_data = {
            "a": True,
            "b.test": 1,
            "b.foo": 2,
            "c.test.x": 10,
            "c.foo.y": 11,
            "c.bar.z": 12,
        }
        self.assertEqual(self.preferences.all(), flattened_data)

    def test_get(self):
        # Retrieve root and nested values
        self.assertEqual(self.preferences.get("a"), True)
        self.assertEqual(self.preferences.get("b.test"), 1)
        self.assertEqual(self.preferences.get("c.bar.z"), 12)

        # Invalid values should return None by default
        self.assertIsNone(self.preferences.get("invalid"))
        self.assertIsNone(self.preferences.get("a.invalid"))
        self.assertIsNone(self.preferences.get("b.test.x.invalid"))
        self.assertIsNone(self.preferences.get("b.test.invalid"))

        # Invalid values with a non-None default should return it
        self.assertEqual(self.preferences.get("invalid", 42), 42)
        self.assertEqual(self.preferences.get("a.invalid", 42), 42)
        self.assertEqual(self.preferences.get("b.test.invalid", 42), 42)
        self.assertEqual(self.preferences.get("b.test.x.invalid", 42), 42)

    def test_set(self):
        preferences = self.preferences

        preferences.set("a", "abc")
        preferences.set("c.test.x", "xyz")
        self.assertEqual(preferences.data["a"], "abc")
        self.assertEqual(preferences.data["c"]["test"]["x"], "xyz")

        preferences.set("d", 42)
        preferences.set("b.bar", "value")
        self.assertEqual(preferences.data["d"], 42)
        self.assertEqual(preferences.data["b"]["bar"], "value")

        # Commit a change to the database
        preferences.set("a", 42, commit=True)
        preferences.refresh_from_db()
        self.assertEqual(preferences.data["a"], 42)

        # Try to change a category into a value
        with self.assertRaises(TypeError):
            preferences.set("b", 42)

        # Try to change a value into a category
        with self.assertRaises(TypeError):
            preferences.set("a.test", 42)

    def test_delete(self):
        preferences = self.preferences

        # Delete existing values
        preferences.delete("a")
        preferences.delete("b.foo")
        self.assertTrue("a" not in preferences.data)
        self.assertTrue("foo" not in preferences.data["b"])
        self.assertEqual(preferences.data["b"]["test"], 1)

        # Try to delete an invalid value, nothing should happen
        preferences.delete("invalid")
