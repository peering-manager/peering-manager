from django.contrib.auth.models import Group, User
from django.test import TestCase

from users.filters import GroupFilterSet, UserFilterSet


class GroupTestCase(TestCase):
    queryset = Group.objects.all()
    filterset = GroupFilterSet

    @classmethod
    def setUpTestData(cls):
        Group.objects.bulk_create(
            [Group(name="Group 1"), Group(name="Group 2"), Group(name="Group 3")]
        )

    def test_id(self):
        params = {"id": self.queryset.first().pk}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        params = {"name": "Group 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class UserTestCase(TestCase):
    queryset = User.objects.all()
    filterset = UserFilterSet

    @classmethod
    def setUpTestData(cls):
        User.objects.bulk_create(
            [
                User(
                    username="batman",
                    first_name="Bruce",
                    last_name="Wayne",
                    email="bwayne@wayne-foundation.com",
                    is_staff=True,
                ),
                User(
                    username="alfred",
                    first_name="Alfred",
                    last_name="Pennyworth",
                    email="apennyworth@wayne-foundation.com",
                ),
                User(
                    username="jim",
                    first_name="James",
                    last_name="Gordon",
                    email="jgordon@gcpd.com",
                ),
                User(
                    username="oracle",
                    first_name="Barbara",
                    last_name="Gordon",
                    email="bgordon@wayne-foundation.com",
                ),
                User(
                    username="robin",
                    first_name="Richard John",
                    last_name="Grayson",
                    is_active=False,
                ),
            ]
        )

    def test_id(self):
        params = {"id": self.queryset.first().pk}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_username(self):
        params = {"username": "batman"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_first_name(self):
        params = {"first_name": "Alfred"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_last_name(self):
        params = {"last_name": "Gordon"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_email(self):
        params = {"email": "bwayne@wayne-foundation.com"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_is_staff(self):
        params = {"is_staff": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_is_active(self):
        params = {"is_active": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
