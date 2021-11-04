import uuid

from django.contrib.auth.models import User

from utils.enums import ObjectChangeAction
from utils.models import ObjectChange, Tag
from utils.testing import ViewTestCases


class ObjectChangeTestCase(ViewTestCases.ReadOnlyObjectViewTestCase):
    model = ObjectChange

    test_changelog_object = None
    test_create_object = None
    test_edit_object = None
    test_delete_object = None
    test_bulk_edit_objects = None
    test_bulk_delete_objects = None

    @classmethod
    def setUpTestData(cls):
        tag = Tag(name="Tag 1", slug="tag-1")
        tag.save()

        user = User.objects.create_user(username="testuser2")
        for i in range(1, 4):
            uid = uuid.uuid4()
            change = tag.to_objectchange(ObjectChangeAction.UPDATE)
            change.user = user
            change.request_id = uid
            change.save()


class TagTestCase(ViewTestCases.OrganizationalObjectViewTestCase):
    model = Tag

    test_changelog_object = None

    @classmethod
    def setUpTestData(cls):
        Tag.objects.bulk_create(
            (
                Tag(name="Tag 1", slug="tag-1"),
                Tag(name="Tag 2", slug="tag-2"),
                Tag(name="Tag 3", slug="tag-3"),
            )
        )

        cls.form_data = {
            "name": "Tag 4",
            "slug": "tag-4",
            "color": "c0c0c0",
            "comments": "Some comments",
        }

        cls.bulk_edit_data = {"color": "00ff00"}
