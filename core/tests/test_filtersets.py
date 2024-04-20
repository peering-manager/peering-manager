from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from ..enums import *
from ..filtersets import *
from ..models import *


class DataSourceTestCase(TestCase):
    queryset = DataSource.objects.all()
    filterset = DataSourceFilterSet

    @classmethod
    def setUpTestData(cls):
        data_sources = [
            DataSource(
                name="Data Source 1",
                type="local",
                source_url="file:///var/tmp/source1/",
                status=DataSourceStatus.NEW,
                enabled=True,
                description="foobar1",
            ),
            DataSource(
                name="Data Source 2",
                type="local",
                source_url="file:///var/tmp/source2/",
                status=DataSourceStatus.SYNCHRONISING,
                enabled=True,
                description="foobar2",
            ),
            DataSource(
                name="Data Source 3",
                type="git",
                source_url="https://example.com/git/source3",
                status=DataSourceStatus.COMPLETED,
                enabled=False,
            ),
        ]
        DataSource.objects.bulk_create(data_sources)

    def test_q(self):
        params = {"q": "foobar1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        params = {"name": ["Data Source 1", "Data Source 2"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_description(self):
        params = {"description": ["foobar1", "foobar2"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_type(self):
        params = {"type": ["local"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_enabled(self):
        params = {"enabled": "true"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"enabled": "false"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_status(self):
        params = {"status": [DataSourceStatus.NEW, DataSourceStatus.SYNCHRONISING]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class DataFileTestCase(TestCase):
    queryset = DataFile.objects.all()
    filterset = DataFileFilterSet

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

        data_files = (
            DataFile(
                source=data_sources[0],
                path="dir1/file1.txt",
                size=1000,
                hash="d3435304778be5165dd27620b7153ed9046c5387f0d708d714a4430bb3de35d8",
                updated=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            ),
            DataFile(
                source=data_sources[1],
                path="dir1/file2.txt",
                size=2000,
                hash="e7f0c847c74df6fddaf14e58b4f2be1c06ed19b1e6efb0459d23310d9cdbc674",
                updated=datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
            ),
            DataFile(
                source=data_sources[2],
                path="dir1/file3.txt",
                size=3000,
                hash="45d473494d769d0b2aa64d564d6a31f7ed4501c13d78aaffb3a4160b0d27f383",
                updated=datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc),
            ),
        )
        DataFile.objects.bulk_create(data_files)

    def test_q(self):
        params = {"q": "file1.txt"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_source(self):
        sources = DataSource.objects.all()
        params = {"source_id": [sources[0].pk, sources[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"source": [sources[0].name, sources[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_path(self):
        params = {"path": ["dir1/file1.txt", "dir1/file2.txt"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_size(self):
        params = {"size": [1000, 2000]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_hash(self):
        params = {
            "hash": [
                "d3435304778be5165dd27620b7153ed9046c5387f0d708d714a4430bb3de35d8",
                "e7f0c847c74df6fddaf14e58b4f2be1c06ed19b1e6efb0459d23310d9cdbc674",
            ]
        }
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
