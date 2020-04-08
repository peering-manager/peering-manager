import uuid

from django.contrib.auth.models import User

from utils.constants import OBJECT_CHANGE_ACTION_UPDATE
from utils.filters import ObjectChangeFilterSet, TagFilterSet
from utils.models import ObjectChange, Tag
from utils.testing import StandardTestCases


class ObjectChangeTestCase(StandardTestCases.Filters):
    model = ObjectChange
    filter = ObjectChangeFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.uuids = []

        tag = Tag(name="Tag 1", slug="tag-1")
        tag.save()

        user = User.objects.create_user(username="testuser2")
        for i in range(1, 4):
            uid = uuid.uuid4()
            cls.uuids.append(uid)
            tag.log_change(user, uid, OBJECT_CHANGE_ACTION_UPDATE)

    def test_q(self):
        params = {"q": ""}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 3)
        params = {"q": "testuser2"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 3)

    def test_action(self):
        params = {"action": OBJECT_CHANGE_ACTION_UPDATE}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 3)

    def test_user(self):
        params = {"user": User.objects.get(username="testuser2").id}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 3)

    def test_user_name(self):
        params = {"user_name": "testuser2"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 3)

    def test_request_id(self):
        params = {"request_id": self.uuids[0]}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)


class TagTestCase(StandardTestCases.Filters):
    model = Tag
    filter = TagFilterSet

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
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 3)
        params = {"q": "tag-1"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)

    def test_name(self):
        params = {"name": "Tag 1"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)

    def test_slug(self):
        params = {"slug": "tag-1"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)
