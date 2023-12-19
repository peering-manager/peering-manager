import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from peering.models import AutonomousSystem
from utils.testing import ViewTestCases

from ..enums import ObjectChangeAction
from ..models import IXAPI, ConfigContext, ExportTemplate, ObjectChange, Tag


class ConfigContextTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = ConfigContext

    test_bulk_edit_objects = None

    @classmethod
    def setUpTestData(cls):
        ConfigContext.objects.bulk_create(
            [
                ConfigContext(name="Test 1", data={"test": 1}),
                ConfigContext(name="Test 2", data={"test": 2}),
                ConfigContext(name="Test 3", data={"test": 3}),
            ]
        )

        cls.form_data = {"name": "Test 4", "data": {"test": 4}}


class ExportTemplateTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = ExportTemplate

    test_bulk_edit_objects = None

    @classmethod
    def setUpTestData(cls):
        content_type = ContentType.objects.get_for_model(AutonomousSystem)
        ExportTemplate.objects.bulk_create(
            [
                ExportTemplate(
                    content_type=content_type,
                    name="Test 1",
                    template="{{ dataset | length }}",
                ),
                ExportTemplate(
                    content_type=content_type,
                    name="Test 2",
                    template="{{ dataset | length }}",
                ),
                ExportTemplate(
                    content_type=content_type,
                    name="Test 3",
                    description="Foo",
                    template="{{ dataset | length }}",
                ),
            ]
        )

        cls.form_data = {
            "content_type": content_type.pk,
            "name": "Test 4",
            "template": "foo",
        }


class IXAPITestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = IXAPI

    test_bulk_edit_objects = None

    @classmethod
    def setUpTestData(cls):
        IXAPI.objects.bulk_create(
            [
                IXAPI(
                    name="IXP 1",
                    url="https://ixp1-ixapi.example.net/v1/",
                    api_key="key-ixp1",
                    api_secret="secret-ixp1",
                    identity="1234",
                ),
                IXAPI(
                    name="IXP 2",
                    url="https://ixp2-ixapi.example.net/v2/",
                    api_key="key-ixp2",
                    api_secret="secret-ixp2",
                    identity="1234",
                ),
                IXAPI(
                    name="IXP 3",
                    url="https://ixp3-ixapi.example.net/v3/",
                    api_key="key-ixp3",
                    api_secret="secret-ixp3",
                    identity="1234",
                ),
            ]
        )

        cls.form_data = {
            "name": "IXP 4",
            "url": "https://ixp4-ixapi.example.net/v1/",
            "api_key": "key-ixp4",
            "api_secret": "secret-ixp4",
            "identity": "1234",
        }

    @patch("extras.models.ixapi.IXAPI.version", return_value=1)
    def test_get_object_anonymous(self, *_):
        with patch(
            "extras.models.ixapi.IXAPI.get_accounts",
            return_value=[
                {"id": "1234", "name": "Account 1"},
                {"id": "5678", "name": "Account 2"},
            ],
        ):
            super().test_get_object_anonymous()

    @patch("extras.models.ixapi.IXAPI.version", return_value=1)
    def test_get_object_with_permission(self, *_):
        with patch(
            "extras.models.ixapi.IXAPI.get_accounts",
            return_value=[
                {"id": "1234", "name": "Account 1"},
                {"id": "5678", "name": "Account 2"},
            ],
        ):
            super().test_get_object_with_permission()

    def test_create_object_with_permission(self):
        with patch("extras.models.ixapi.IXAPI.test_connectivity", return_value=True):
            super().test_create_object_with_permission()

    def test_edit_object_with_permission(self):
        with patch("extras.models.ixapi.IXAPI.test_connectivity", return_value=True):
            super().test_edit_object_with_permission()


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
            "description": "Some description",
        }

        cls.bulk_edit_data = {"color": "00ff00"}
