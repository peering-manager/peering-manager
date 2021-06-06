from django.test import TestCase

from extras.filters import WebhookFilterSet
from extras.models import Webhook


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
                url="https://example.com/?1",
                http_method="GET",
                ssl_verification=True,
            ),
            Webhook(
                name="Webhook 2",
                type_update=True,
                enabled=True,
                url="https://example.com/?2",
                http_method="POST",
                ssl_verification=True,
            ),
            Webhook(
                name="Webhook 3",
                type_delete=True,
                enabled=False,
                http_method="PATCH",
                url="https://example.com/?3",
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
