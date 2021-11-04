import uuid

from django.contrib.auth.models import User
from django.test import TestCase

from utils.enums import ObjectChangeAction
from utils.filters import ObjectChangeFilterSet, TagFilterSet
from utils.models import ObjectChange, Tag
from utils.testing.filtersets import BaseFilterSetTests


class ObjectChangeTestCase(TestCase, BaseFilterSetTests):
    queryset = ObjectChange.objects.all()
    filterset = ObjectChangeFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.uuids = []

        tag = Tag(name="Tag 1", slug="tag-1")
        tag.save()

        user = User.objects.create_user(username="testuser2")
        for i in range(1, 4):
            uid = uuid.uuid4()
            cls.uuids.append(uid)
            change = tag.to_objectchange(ObjectChangeAction.UPDATE)
            change.user = user
            change.request_id = uid
            change.save()

    def test_q(self):
        params = {"q": ""}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"q": "testuser2"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_action(self):
        params = {"action": ObjectChangeAction.UPDATE}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_user_id(self):
        params = {"user_id": User.objects.get(username="testuser2").id}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_user_name(self):
        params = {"user": "testuser2"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_request_id(self):
        params = {"request_id": self.uuids[0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class TagTestCase(TestCase, BaseFilterSetTests):
    queryset = Tag.objects.all()
    filterset = TagFilterSet

    @classmethod
    def setUpTestData(cls):
        Tag.objects.bulk_create(
            (
                Tag(name="Tag 1", slug="tag-1"),
                Tag(name="Tag 2", slug="tag-2"),
                Tag(name="Tag 3", slug="tag-3"),
            )
        )

    def test_q(self):
        params = {"q": ""}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"q": "tag-1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
