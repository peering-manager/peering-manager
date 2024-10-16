import uuid

from django.contrib.auth.models import User
from django.utils import timezone

from extras.models import Tag
from utils.testing import ViewTestCases

from ..enums import *
from ..models import *


class DataSourceTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = DataSource

    @classmethod
    def setUpTestData(cls):
        data_sources = [
            DataSource(
                name="Data Source 1",
                type="local",
                source_url="file:///var/tmp/source1/",
            ),
            DataSource(
                name="Data Source 2",
                type="local",
                source_url="file:///var/tmp/source2/",
            ),
            DataSource(
                name="Data Source 3",
                type="local",
                source_url="file:///var/tmp/source3/",
            ),
        ]
        DataSource.objects.bulk_create(data_sources)

        cls.form_data = {
            "name": "Data Source X",
            "type": "git",
            "source_url": "http:///exmaple/com/foo/bar/",
            "description": "Something",
            "comments": "Foo bar baz",
        }

        cls.bulk_edit_data = {"enabled": False, "description": "New description"}


class DataFileTestCase(
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
):
    model = DataFile

    @classmethod
    def setUpTestData(cls):
        data_source = DataSource.objects.create(
            name="Data Source 1", type="local", source_url="file:///var/tmp/source1/"
        )

        data_files = [
            DataFile(
                source=data_source,
                path="dir1/file1.txt",
                updated=timezone.now(),
                size=1000,
                hash="d3435304778be5165dd27620b7153ed9046c5387f0d708d714a4430bb3de35d8",
            ),
            DataFile(
                source=data_source,
                path="dir1/file2.txt",
                updated=timezone.now(),
                size=2000,
                hash="e7f0c847c74df6fddaf14e58b4f2be1c06ed19b1e6efb0459d23310d9cdbc674",
            ),
            DataFile(
                source=data_source,
                path="dir1/file3.txt",
                updated=timezone.now(),
                size=3000,
                hash="45d473494d769d0b2aa64d564d6a31f7ed4501c13d78aaffb3a4160b0d27f383",
            ),
        ]
        DataFile.objects.bulk_create(data_files)


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
        for _ in range(3):
            uid = uuid.uuid4()
            change = tag.to_objectchange(ObjectChangeAction.UPDATE)
            change.user = user
            change.request_id = uid
            change.save()
