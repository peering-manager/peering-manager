import uuid

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from utils.testing import APITestCase, APIViewTestCases

from ..models import DataFile, DataSource, Job


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("core-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DataSourceTest(APIViewTestCases.View):
    model = DataSource
    brief_fields = ["id", "url", "display_url", "display", "name"]
    create_data = [
        {
            "name": "Data Source 4",
            "type": "git",
            "source_url": "https://example.com/git/source4",
        },
        {
            "name": "Data Source 5",
            "type": "git",
            "source_url": "https://example.com/git/source5",
        },
        {
            "name": "Data Source 6",
            "type": "git",
            "source_url": "https://example.com/git/source6",
        },
    ]
    bulk_update_data = {"enabled": False, "description": "foo bar baz"}

    @classmethod
    def setUpTestData(cls):
        DataSource.objects.bulk_create(
            [
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
        )


class DataFileTest(APIViewTestCases.GetObjectView, APIViewTestCases.ListObjectsView):
    model = DataFile
    brief_fields = ["id", "url", "display_url", "display", "path"]

    @classmethod
    def setUpTestData(cls):
        datasource = DataSource.objects.create(
            name="Data Source 1", type="local", source_url="file:///var/tmp/source1/"
        )
        DataFile.objects.bulk_create(
            [
                DataFile(
                    source=datasource,
                    path="dir1/file1.txt",
                    size=1000,
                    hash="442da078f0111cbdf42f21903724f6597c692535f55bdfbbea758a1ae99ad9e1",
                    updated=timezone.now(),
                ),
                DataFile(
                    source=datasource,
                    path="dir1/file2.txt",
                    size=2000,
                    hash="a78168c7c97115bafd96450ed03ea43acec495094c5caa28f0d02e20e3a76cc2",
                    updated=timezone.now(),
                ),
                DataFile(
                    source=datasource,
                    path="dir1/file3.txt",
                    size=3000,
                    hash="12b8827a14c4d5a2f30b6c6e2b7983063988612391c6cbe8ee7493b59054827a",
                    updated=timezone.now(),
                ),
            ]
        )


class JobTest(APIViewTestCases.GetObjectView, APIViewTestCases.ListObjectsView):
    model = Job
    brief_fields = [
        "id",
        "url",
        "display_url",
        "display",
        "created",
        "completed",
        "user",
        "status",
    ]

    @classmethod
    def setUpTestData(cls):
        Job.objects.create(
            name="test",
            object_type=ContentType.objects.get_for_model(Job),
            user=None,
            job_id=uuid.uuid4(),
        )
