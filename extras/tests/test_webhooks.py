import json
import uuid
from unittest.mock import patch

import django_rq
from django.http import HttpResponse
from django.urls import reverse
from requests import Session
from rest_framework import status

from extras.models import Webhook
from extras.webhooks import enqueue_object, flush_webhooks, generate_signature
from extras.workers import generate_signature, process_webhook
from peering.models import AutonomousSystem
from utils.enums import ObjectChangeAction
from utils.models import Tag
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
                    name="Create Webhook",
                    type_create=True,
                    url=TEST_URL,
                    secret=TEST_SECRET,
                ),
                Webhook(
                    name="Update Webhook",
                    type_update=True,
                    url=TEST_URL,
                    secret=TEST_SECRET,
                ),
                Webhook(
                    name="Delete Webhook",
                    type_delete=True,
                    url=TEST_URL,
                    secret=TEST_SECRET,
                ),
            ]
        )
        Tag.objects.bulk_create(
            (
                Tag(name="Foo", slug="foo"),
                Tag(name="Bar", slug="bar"),
                Tag(name="Baz", slug="baz"),
            )
        )

    def test_enqueue_webhook_create(self):
        data = {
            "asn": 64500,
            "name": "AS 1",
            "tags": [
                {"name": "Foo"},
                {"name": "Bar"},
            ],
        }
        url = reverse("peering-api:autonomoussystem-list")
        response = self.client.post(url, data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(AutonomousSystem.objects.count(), 1)
        self.assertEqual(AutonomousSystem.objects.first().tags.count(), 2)

        # Verify that a job was queued for the object creation webhook
        self.assertEqual(self.queue.count, 1)
        job = self.queue.jobs[0]
        self.assertEqual(job.kwargs["webhook"], Webhook.objects.get(type_create=True))
        self.assertEqual(job.kwargs["event"], ObjectChangeAction.CREATE)
        self.assertEqual(job.kwargs["model_name"], "autonomoussystem")
        self.assertEqual(job.kwargs["data"]["id"], response.data["id"])
        self.assertEqual(len(job.kwargs["data"]["tags"]), len(response.data["tags"]))
        self.assertEqual(job.kwargs["snapshots"]["postchange"]["name"], "AS 1")
        self.assertEqual(
            sorted(job.kwargs["snapshots"]["postchange"]["tags"]), ["Bar", "Foo"]
        )

    def test_enqueue_webhook_bulk_create(self):
        # Create multiple objects via the REST API
        data = [
            {
                "asn": 64500,
                "name": "AS 1",
                "tags": [
                    {"name": "Foo"},
                    {"name": "Bar"},
                ],
            },
            {
                "asn": 64501,
                "name": "AS 2",
                "tags": [
                    {"name": "Foo"},
                    {"name": "Bar"},
                ],
            },
            {
                "asn": 64502,
                "name": "AS 3",
                "tags": [
                    {"name": "Foo"},
                    {"name": "Bar"},
                ],
            },
        ]
        url = reverse("peering-api:autonomoussystem-list")
        response = self.client.post(url, data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(AutonomousSystem.objects.count(), 3)
        self.assertEqual(AutonomousSystem.objects.first().tags.count(), 2)

        # Verify that a webhook was queued for each object
        self.assertEqual(self.queue.count, 3)
        for i, job in enumerate(self.queue.jobs):
            self.assertEqual(
                job.kwargs["webhook"], Webhook.objects.get(type_create=True)
            )
            self.assertEqual(job.kwargs["event"], ObjectChangeAction.CREATE)
            self.assertEqual(job.kwargs["model_name"], "autonomoussystem")
            self.assertEqual(job.kwargs["data"]["id"], response.data[i]["id"])
            self.assertEqual(
                len(job.kwargs["data"]["tags"]), len(response.data[i]["tags"])
            )
            self.assertEqual(
                job.kwargs["snapshots"]["postchange"]["name"], response.data[i]["name"]
            )
            self.assertEqual(
                sorted(job.kwargs["snapshots"]["postchange"]["tags"]), ["Bar", "Foo"]
            )

    def test_enqueue_webhook_update(self):
        asn = AutonomousSystem.objects.create(asn=64500, name="AS 1")
        asn.tags.set(Tag.objects.filter(name__in=["Foo", "Bar"]))

        # Update an object via the REST API
        data = {
            "name": "My AS",
            "comments": "Updated the AS",
            "tags": [{"name": "Baz"}],
        }
        url = reverse("peering-api:autonomoussystem-detail", kwargs={"pk": asn.pk})
        response = self.client.patch(url, data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)

        # Verify that a job was queued for the object update webhook
        self.assertEqual(self.queue.count, 1)
        job = self.queue.jobs[0]
        self.assertEqual(job.kwargs["webhook"], Webhook.objects.get(type_update=True))
        self.assertEqual(job.kwargs["event"], ObjectChangeAction.UPDATE)
        self.assertEqual(job.kwargs["model_name"], "autonomoussystem")
        self.assertEqual(job.kwargs["data"]["id"], asn.pk)
        self.assertEqual(len(job.kwargs["data"]["tags"]), len(response.data["tags"]))
        self.assertEqual(job.kwargs["snapshots"]["prechange"]["name"], "AS 1")
        self.assertEqual(
            sorted(job.kwargs["snapshots"]["prechange"]["tags"]), ["Bar", "Foo"]
        )
        self.assertEqual(job.kwargs["snapshots"]["postchange"]["name"], "My AS")
        self.assertEqual(sorted(job.kwargs["snapshots"]["postchange"]["tags"]), ["Baz"])

    def test_enqueue_webhook_bulk_update(self):
        asns = (
            AutonomousSystem(asn=64500, name="AS 1"),
            AutonomousSystem(asn=64501, name="AS 2"),
            AutonomousSystem(asn=64502, name="AS 3"),
        )
        AutonomousSystem.objects.bulk_create(asns)
        for asn in asns:
            asn.tags.set(Tag.objects.filter(name__in=["Foo", "Bar"]))

        # Update three objects via the REST API
        data = [
            {"id": asns[0].pk, "name": "ASN 1", "tags": [{"name": "Baz"}]},
            {"id": asns[1].pk, "name": "ASN 2", "tags": [{"name": "Baz"}]},
            {"id": asns[2].pk, "name": "ASN 3", "tags": [{"name": "Baz"}]},
        ]
        url = reverse("peering-api:autonomoussystem-list")
        response = self.client.patch(url, data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)

        # Verify that a job was queued for the object update webhook
        self.assertEqual(self.queue.count, 3)
        for i, job in enumerate(self.queue.jobs):
            self.assertEqual(
                job.kwargs["webhook"], Webhook.objects.get(type_update=True)
            )
            self.assertEqual(job.kwargs["event"], ObjectChangeAction.UPDATE)
            self.assertEqual(job.kwargs["model_name"], "autonomoussystem")
            self.assertEqual(job.kwargs["data"]["id"], data[i]["id"])
            self.assertEqual(
                len(job.kwargs["data"]["tags"]), len(response.data[i]["tags"])
            )
            self.assertEqual(job.kwargs["snapshots"]["prechange"]["name"], asns[i].name)
            self.assertEqual(
                sorted(job.kwargs["snapshots"]["prechange"]["tags"]), ["Bar", "Foo"]
            )
            self.assertEqual(
                job.kwargs["snapshots"]["postchange"]["name"], response.data[i]["name"]
            )
            self.assertEqual(
                sorted(job.kwargs["snapshots"]["postchange"]["tags"]), ["Baz"]
            )

    def test_enqueue_webhook_delete(self):
        asn = AutonomousSystem.objects.create(asn=64500, name="AS 1")
        asn.tags.set(Tag.objects.filter(name__in=["Foo", "Bar"]))

        # Delete an object via the REST API
        url = reverse("peering-api:autonomoussystem-detail", kwargs={"pk": asn.pk})
        response = self.client.delete(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_204_NO_CONTENT)

        # Verify that a job was queued for the object update webhook
        self.assertEqual(self.queue.count, 1)
        job = self.queue.jobs[0]
        self.assertEqual(job.kwargs["webhook"], Webhook.objects.get(type_delete=True))
        self.assertEqual(job.kwargs["event"], ObjectChangeAction.DELETE)
        self.assertEqual(job.kwargs["model_name"], "autonomoussystem")
        self.assertEqual(job.kwargs["data"]["id"], asn.pk)
        self.assertEqual(job.kwargs["snapshots"]["prechange"]["name"], "AS 1")
        self.assertEqual(
            sorted(job.kwargs["snapshots"]["prechange"]["tags"]), ["Bar", "Foo"]
        )

    def test_enqueue_webhook_bulk_delete(self):
        asns = (
            AutonomousSystem(asn=64500, name="AS 1"),
            AutonomousSystem(asn=64501, name="AS 2"),
            AutonomousSystem(asn=64502, name="AS 3"),
        )
        AutonomousSystem.objects.bulk_create(asns)
        for asn in asns:
            asn.tags.set(Tag.objects.filter(name__in=["Foo", "Bar"]))

        # Delete three objects via the REST API
        data = [{"id": asn.pk} for asn in asns]
        url = reverse("peering-api:autonomoussystem-list")
        response = self.client.delete(url, data, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_204_NO_CONTENT)

        # Verify that a job was queued for the object update webhook
        self.assertEqual(self.queue.count, 3)
        for i, job in enumerate(self.queue.jobs):
            self.assertEqual(
                job.kwargs["webhook"], Webhook.objects.get(type_delete=True)
            )
            self.assertEqual(job.kwargs["event"], ObjectChangeAction.DELETE)
            self.assertEqual(job.kwargs["model_name"], "autonomoussystem")
            self.assertEqual(job.kwargs["data"]["id"], asns[i].pk)
            self.assertEqual(job.kwargs["snapshots"]["prechange"]["name"], asns[i].name)
            self.assertEqual(
                sorted(job.kwargs["snapshots"]["prechange"]["tags"]), ["Bar", "Foo"]
            )

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
            self.assertEqual(body["timestamp"], job.kwargs["timestamp"])
            self.assertEqual(body["model"], "autonomoussystem")
            self.assertEqual(body["username"], "testuser")
            self.assertEqual(body["request_id"], str(request_id))
            self.assertEqual(body["data"]["name"], "AS 1")

            return HttpResponse()

        # Enqueue a webhook for processing
        webhooks_queue = []
        asn = AutonomousSystem.objects.create(asn=64500, name="AS 1")
        enqueue_object(
            webhooks_queue,
            instance=asn,
            user=self.user,
            request_id=request_id,
            action=ObjectChangeAction.CREATE,
        )
        flush_webhooks(webhooks_queue)

        # Retrieve the job from queue
        job = self.queue.jobs[0]

        # Patch the Session object with our dummy_send() method, then process the webhook for sending
        with patch.object(Session, "send", mock_send) as mock_send:
            process_webhook(**job.kwargs)
