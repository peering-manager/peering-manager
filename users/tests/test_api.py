from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework import status

from utils.functions import merge_hash
from utils.testing import APITestCase, APIViewTestCases


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("users-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GroupTest(APIViewTestCases.View):
    model = Group
    view_namespace = "users"
    query_fields = ["id", "url", "display"]
    brief_fields = ["id", "url", "display", "name"]
    create_data = [{"name": "Group 4"}, {"name": "Group 5"}, {"name": "Group 6"}]

    @classmethod
    def setUpTestData(cls):
        Group.objects.bulk_create(
            [Group(name="Group 1"), Group(name="Group 2"), Group(name="Group 3")]
        )


class UserTest(APIViewTestCases.View):
    model = User
    view_namespace = "users"
    query_fields = ["id", "url", "display"]
    brief_fields = ["id", "url", "display", "username"]
    validation_excluded_fields = ["password"]
    create_data = [
        {"username": "user4", "password": "password4"},
        {"username": "user5", "password": "password5"},
        {"username": "user6", "password": "password6"},
    ]

    @classmethod
    def setUpTestData(cls):
        User.objects.bulk_create(
            [
                User(username="user1", password="password1"),
                User(username="user2", password="password2"),
                User(username="user3", password="password3"),
            ]
        )


class UserPreferencesTest(APITestCase):
    def test_get(self):
        """
        Retrieve user configuration via GET request.
        """
        preferences = self.user.preferences
        url = reverse("users-api:userpref-list")

        response = self.client.get(url, **self.header)
        self.assertEqual(response.data, {})

        data = {"a": 123, "b": 456, "c": 789}
        preferences.data = data
        preferences.save()
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data, data)

    def test_patch(self):
        """
        Set user config via PATCH requests.
        """
        preferences = self.user.preferences
        url = reverse("users-api:userpref-list")

        data = {
            "a": {"a1": "X", "a2": "Y"},
            "b": {"b1": "Z"},
        }
        response = self.client.patch(url, data=data, format="json", **self.header)
        self.assertDictEqual(response.data, data)
        preferences.refresh_from_db()
        self.assertDictEqual(preferences.data, data)

        update_data = {"c": 123}
        response = self.client.patch(
            url, data=update_data, format="json", **self.header
        )
        new_data = merge_hash(data, update_data)
        self.assertDictEqual(response.data, new_data)
        preferences.refresh_from_db()
        self.assertDictEqual(preferences.data, new_data)
