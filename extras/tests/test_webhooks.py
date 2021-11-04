import json
import uuid
from unittest.mock import patch

import django_rq
from django.http import HttpResponse
from django.urls import reverse
from requests import Session
from rest_framework import status

from extras.models import Webhook
from extras.workers import enqueue_webhooks, generate_signature, process_webhook
from peering.models import AutonomousSystem
from utils.enums import ObjectChangeAction
from utils.testing import APITestCase


class WebhookTest(APITestCase):
    def setUp(self):
        super().setUp()

        # Make sure the queue is empty before testing
        self.queue = django_rq.get_queue("default")
        self.queue.empty()

    @classmethod
    def setUpTestData(cls):
        TEST_URL = "http://localhost/"
        TEST_SECRET = "thisisaverystrongsecret"

        webhooks = Webhook.objects.bulk_create(
            [
                Webhook(
                    name="AS Create Webhook",
                    type_create=True,
                    url=TEST_URL,
                    secret=TEST_SECRET,
                ),
                Webhook(
                    name="AS Update Webhook",
                    type_update=True,
                    url=TEST_URL,
                    secret=TEST_SECRET,
                ),
                Webhook(
                    name="AS Delete Webhook",
                    type_delete=True,
                    url=TEST_URL,
                    secret=TEST_SECRET,
                ),
            ]
        )

    def test_enqueue_webhook_create(self):
        data = {"asn": 201281, "name": "Guillaume Mazoyer"}
        url = reverse("peering-api:autonomoussystem-list")
        response = self.client.post(url, data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(AutonomousSystem.objects.count(), 1)

        # Verify that a job was queued for the object creation webhook
        self.assertEqual(self.queue.count, 1)
        job = self.queue.jobs[0]
        self.assertEqual(job.args[0], Webhook.objects.get(type_create=True))
        self.assertEqual(job.args[1]["id"], response.data["id"])
        self.assertEqual(job.args[2], "autonomoussystem")
        self.assertEqual(job.args[3], ObjectChangeAction.CREATE)

    def test_enqueue_webhook_update(self):
        a_s = AutonomousSystem.objects.create(asn=201281, name="Guillaume Mazoyer")
        data = {"comments": "Updated the AS"}
        url = reverse("peering-api:autonomoussystem-detail", kwargs={"pk": a_s.pk})
        response = self.client.patch(url, data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)

        # Verify that a job was queued for the object update webhook
        self.assertEqual(self.queue.count, 1)
        job = self.queue.jobs[0]
        self.assertEqual(job.args[0], Webhook.objects.get(type_update=True))
        self.assertEqual(job.args[1]["id"], a_s.pk)
        self.assertEqual(job.args[2], "autonomoussystem")
        self.assertEqual(job.args[3], ObjectChangeAction.UPDATE)

    def test_enqueue_webhook_delete(self):
        a_s = AutonomousSystem.objects.create(asn=201281, name="Guillaume Mazoyer")
        url = reverse("peering-api:autonomoussystem-detail", kwargs={"pk": a_s.pk})
        response = self.client.delete(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_204_NO_CONTENT)

        # Verify that a job was queued for the object deletion webhook
        self.assertEqual(self.queue.count, 1)
        job = self.queue.jobs[0]
        self.assertEqual(job.args[0], Webhook.objects.get(type_delete=True))
        self.assertEqual(job.args[1]["id"], a_s.pk)
        self.assertEqual(job.args[2], "autonomoussystem")
        self.assertEqual(job.args[3], ObjectChangeAction.DELETE)

    def test_worker(self):
        request_id = uuid.uuid4()

        def mock_send(_, request, **kwargs):
            """
            Mocked implementation of Session.send() that always returns a 200 HTTP
            status code.
            """
            webhook = Webhook.objects.get(type_create=True)
            signature = generate_signature(request.body, webhook.secret)

            # Validate the outgoing request headers
            self.assertEqual(request.headers["Content-Type"], webhook.http_content_type)
            self.assertEqual(request.headers["X-Hook-Signature"], signature)

            # Validate the outgoing request body
            body = json.loads(request.body)
            self.assertEqual(body["event"], ObjectChangeAction.CREATE)
            self.assertEqual(body["timestamp"], job.args[4])
            self.assertEqual(body["model"], "autonomoussystem")
            self.assertEqual(body["username"], "testuser")
            self.assertEqual(body["request_id"], str(request_id))
            self.assertEqual(body["data"]["name"], "Guillaume Mazoyer")

            return HttpResponse()

        # Enqueue a webhook for processing
        a_s = AutonomousSystem.objects.create(asn=201281, name="Guillaume Mazoyer")
        enqueue_webhooks(a_s, self.user, request_id, ObjectChangeAction.CREATE)

        job = self.queue.jobs[0]
        with patch.object(Session, "send", mock_send):
            process_webhook(*job.args)
