import uuid

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status

from extras.models import JobResult, Webhook
from utils.testing import APITestCase, StandardAPITestCases


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("extras-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class StaticChoiceTest(APITestCase):
    def test_list_static_choices(self):
        url = reverse("extras-api:field-choice-list")
        response = self.client.get(url, **self.header)
        self.assertEqual(len(response.data), 1)


class JobResultTest(
    StandardAPITestCases.GetObjectView, StandardAPITestCases.ListObjectsView
):
    model = JobResult
    brief_fields = ["url", "created", "completed", "user", "status"]

    @classmethod
    def setUpTestData(cls):
        JobResult.objects.create(
            name="test",
            obj_type=ContentType.objects.get_for_model(JobResult),
            user=None,
            job_id=uuid.uuid4(),
        )


class WebhookTest(StandardAPITestCases.View):
    model = Webhook
    brief_fields = ["id", "name", "url"]
    create_data = [
        {"name": "Webhook 4", "type_create": True, "url": "http://example.com/?4"},
        {"name": "Webhook 5", "type_update": True, "url": "http://example.com/?5"},
        {"name": "Webhook 6", "type_delete": True, "url": "http://example.com/?6"},
    ]
    bulk_update_data = {"ssl_verification": False}

    @classmethod
    def setUpTestData(cls):
        webhooks = (
            Webhook(name="Webhook 1", type_create=True, url="http://example.com/?1"),
            Webhook(name="Webhook 2", type_update=True, url="http://example.com/?2"),
            Webhook(name="Webhook 3", type_delete=True, url="http://example.com/?3"),
        )
        Webhook.objects.bulk_create(webhooks)
