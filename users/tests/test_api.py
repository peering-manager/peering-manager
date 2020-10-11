from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework import status


from peering.models import AutonomousSystem
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
        User.objects.create(username="User_1")
        User.objects.bulk_create([User(username="User_2"), User(username="User_3")])

    def test_set_context_asn(self):
        affiliated = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        AutonomousSystem.objects.create(asn=65000, name="ACME")
        user = User.objects.get(username="User_1")

        url = reverse(
            "users-api:user-set-context-asn",
            kwargs={"pk": user.pk},
        )

        data = {"asn": 201281}
        response = self.client.patch(url, data, format="json", **self.header)
        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(user.preferences.get("context.asn"), affiliated.pk)

        data = {"asn": 65000}
        response = self.client.patch(url, data, format="json", **self.header)
        self.assertStatus(response, status.HTTP_404_NOT_FOUND)
        self.assertEqual(user.preferences.get("context.asn"), affiliated.pk)
