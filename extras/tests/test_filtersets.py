from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from peering.models import AutonomousSystem
from utils.testing import BaseFilterSetTests

from ..filtersets import (
    ConfigContextAssignmentFilterSet,
    ConfigContextFilterSet,
    ExportTemplateFilterSet,
    TagFilterSet,
    WebhookFilterSet,
)
from ..models import (
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    Tag,
    Webhook,
)


class ConfigContextTestCase(TestCase):
    queryset = ConfigContext.objects.all()
    filterset = ConfigContextFilterSet

    @classmethod
    def setUpTestData(cls):
        config_contexts = [
            ConfigContext(
                name="Test 1", description="This is test 1", data={"test": 1}
            ),
            ConfigContext(
                name="Test 2", description="This is test 2", data={"test": 2}
            ),
            ConfigContext(
                name="Test 3",
                description="This is test 3",
                is_active=False,
                data={"test": 3},
            ),
        ]
        ConfigContext.objects.bulk_create(config_contexts)

    def test_id(self):
        params = {"id": self.queryset.values_list("pk", flat=True)[:2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {"name": ["Test 1", "Test 2"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_description(self):
        params = {"description": ["This is test 1", "This is test 2"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_is_active(self):
        params = {"is_active": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"is_active": False}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class ConfigContextAssignmentTestCase(TestCase):
    queryset = ConfigContextAssignment.objects.all()
    filterset = ConfigContextAssignmentFilterSet

    @classmethod
    def setUpTestData(cls):
        asns = [
            AutonomousSystem(name="Foo", asn=64501),
            AutonomousSystem(name="Bar", asn=64502),
        ]
        AutonomousSystem.objects.bulk_create(asns)

        config_contexts = [
            ConfigContext(name="Test 1", data={"test": True}),
            ConfigContext(name="Test 2", data={"test": True}),
            ConfigContext(name="Test 3", data={"test": False}),
        ]
        ConfigContext.objects.bulk_create(config_contexts)

        config_context_assignments = [
            ConfigContextAssignment(
                object=asns[0], config_context=config_contexts[0], weight=1000
            ),
            ConfigContextAssignment(
                object=asns[0], config_context=config_contexts[1], weight=1000
            ),
            ConfigContextAssignment(
                object=asns[1], config_context=config_contexts[2], weight=2000
            ),
        ]
        ConfigContextAssignment.objects.bulk_create(config_context_assignments)

    def test_id(self):
        params = {"id": self.queryset.values_list("pk", flat=True)[:2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_object_id(self):
        params = {"object_id": [AutonomousSystem.objects.first().pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_weight(self):
        params = {"weight": [1000]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"weight": [2000]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class ExportTemplateTestCase(TestCase):
    queryset = ExportTemplate.objects.all()
    filterset = ExportTemplateFilterSet

    @classmethod
    def setUpTestData(cls):
        content_type = ContentType.objects.get_for_model(AutonomousSystem)
        export_templates = [
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
        ExportTemplate.objects.bulk_create(export_templates)

    def test_id(self):
        params = {"id": self.queryset.values_list("pk", flat=True)[:2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {"name": ["Test 1", "Test 2"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_description(self):
        params = {"description": ["Foo"]}
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


class WebhookTestCase(TestCase):
    queryset = Webhook.objects.all()
    filterset = WebhookFilterSet

    @classmethod
    def setUpTestData(cls):
        webhooks = (
            Webhook(
                name="Webhook 1",
                type_create=True,
                enabled=True,
                payload_url="https://example.com/1",
                http_method="GET",
                ssl_verification=True,
            ),
            Webhook(
                name="Webhook 2",
                type_update=True,
                enabled=True,
                payload_url="https://example.com/2",
                http_method="POST",
                ssl_verification=True,
            ),
            Webhook(
                name="Webhook 3",
                type_delete=True,
                enabled=False,
                http_method="PATCH",
                payload_url="https://example.com/3",
                ssl_verification=False,
            ),
        )
        Webhook.objects.bulk_create(webhooks)

    def test_id(self):
        params = {"id": self.queryset.values_list("pk", flat=True)[:2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {"name": ["Webhook 1", "Webhook 2"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_type_create(self):
        params = {"type_create": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_type_update(self):
        params = {"type_update": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_type_delete(self):
        params = {"type_delete": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_enabled(self):
        params = {"enabled": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_http_method(self):
        params = {"http_method": ["GET", "POST"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_ssl_verification(self):
        params = {"ssl_verification": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
