from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework import status

from utils.testing import APITestCase, StandardAPITestCases


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("users-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GroupTest(StandardAPITestCases.View):
    model = Group
    view_namespace = "users"
    brief_fields = ["id", "name", "url"]
    create_data = [
        {"name": "Group 4"},
        {"name": "Group 5"},
        {"name": "Group 6"},
    ]

    @classmethod
    def setUpTestData(cls):
        Group.objects.bulk_create(
            [Group(name="Group 1"), Group(name="Group 2"), Group(name="Group 3")]
        )


class UserTest(StandardAPITestCases.View):
    model = User
    view_namespace = "users"
    brief_fields = ["id", "url", "username"]
    create_data = [
        {"username": "User_4"},
        {"username": "User_5"},
        {"username": "User_6"},
    ]

    @classmethod
    def setUpTestData(cls):
        User.objects.bulk_create(
            [User(username="User_1"), User(username="User_2"), User(username="User_3")]
        )
