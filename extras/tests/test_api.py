from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status

from peering.models import AutonomousSystem
from peering.tests.mocked_data import mocked_subprocess_popen
from utils.testing import APITestCase, APIViewTestCases, MockedResponse

from ..models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    JournalEntry,
    Tag,
    Webhook,
)


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("extras-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ConfigContextTest(APIViewTestCases.View):
    model = ConfigContext
    brief_fields = ["id", "url", "display_url", "display", "name"]

    @classmethod
    def setUpTestData(cls):
        config_contexts = [
            ConfigContext(name="Test 1", data={"test": True}),
            ConfigContext(name="Test 2", data={"test": True}),
            ConfigContext(name="Test 3", data={"test": True}),
        ]
        ConfigContext.objects.bulk_create(config_contexts)

        cls.create_data = [
            {"name": "Test 4", "data": {"test": False}},
            {"name": "Test 5", "data": {"test": False}},
            {"name": "Test 6", "data": {"test": False}},
        ]


class ConfigContextAssignmentTest(APIViewTestCases.View):
    model = ConfigContextAssignment
    query_fields = ["id", "url", "display"]
    brief_fields = ["id", "url", "display", "config_context"]

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
            ConfigContext(name="Test 3", data={"test": True}),
            ConfigContext(name="Test 4", data={"test": False}),
            ConfigContext(name="Test 5", data={"test": False}),
            ConfigContext(name="Test 6", data={"test": False}),
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
                object=asns[0], config_context=config_contexts[2], weight=1000
            ),
        ]
        ConfigContextAssignment.objects.bulk_create(config_context_assignments)

        cls.create_data = [
            {
                "content_type": "peering.autonomoussystem",
                "object_id": asns[1].pk,
                "config_context": config_contexts[3].pk,
                "weight": 1000,
            },
            {
                "content_type": "peering.autonomoussystem",
                "object_id": asns[1].pk,
                "config_context": config_contexts[4].pk,
                "weight": 1000,
            },
            {
                "content_type": "peering.autonomoussystem",
                "object_id": asns[1].pk,
                "config_context": config_contexts[5].pk,
                "weight": 1000,
            },
        ]


class ExportTemplateTest(APIViewTestCases.View):
    model = ExportTemplate
    brief_fields = ["id", "url", "display_url", "display", "name"]

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
                template="{{ dataset | length }}",
            ),
        ]
        ExportTemplate.objects.bulk_create(export_templates)

        cls.create_data = [
            {
                "content_type": "peering.bgpgroup",
                "name": "Test 4",
                "template": "nothing to see",
            },
            {
                "content_type": "peering.bgpgroup",
                "name": "Test 5",
                "template": "nothing to see",
            },
            {
                "content_type": "peering.bgpgroup",
                "name": "Test 6",
                "template": "nothing to see",
            },
        ]


class IXAPITest(APIViewTestCases.View):
    model = IXAPI
    brief_fields = ["id", "url", "display_url", "display", "name"]
    create_data = [
        {
            "name": "IXP 4",
            "api_url": "https://ixp4-ixapi.example.net",
            "api_key": "key-ixp4",
            "api_secret": "secret-ixp4",
            "identity": "1234",
        },
        {
            "name": "IXP 5",
            "api_url": "https://ixp5-ixapi.example.net",
            "api_key": "key-ixp5",
            "api_secret": "secret-ixp5",
            "identity": "1234",
        },
        {
            "name": "IXP 6",
            "api_url": "https://ixp6-ixapi.example.net",
            "api_key": "key-ixp6",
            "api_secret": "secret-ixp6",
            "identity": "1234",
        },
    ]

    @classmethod
    def setUpTestData(cls):
        IXAPI.objects.bulk_create(
            [
                IXAPI(
                    name="IXP 1",
                    api_url="https://ixp1-ixapi.example.net/v1/",
                    api_key="key-ixp1",
                    api_secret="secret-ixp1",
                    identity="1234",
                ),
                IXAPI(
                    name="IXP 2",
                    api_url="https://ixp2-ixapi.example.net/v2/",
                    api_key="key-ixp2",
                    api_secret="secret-ixp2",
                    identity="1234",
                ),
                IXAPI(
                    name="IXP 3",
                    api_url="https://ixp3-ixapi.example.net/v3/",
                    api_key="key-ixp3",
                    api_secret="secret-ixp3",
                    identity="1234",
                ),
            ]
        )

    @patch(
        "requests.sessions.Session.post",
        return_value=MockedResponse(
            fixture="extras/tests/fixtures/ix_api/authenticate.json"
        ),
    )
    @patch("pyixapi.core.api.API.version", return_value=1)
    def test_accounts(self, *_):
        ixapi = IXAPI.objects.get(name="IXP 1")
        url = reverse("extras-api:ixapi-accounts")

        # Query params required
        response = self.client.get(url, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

        # With query params
        with patch(
            "pyixapi.core.query.Request.get",
            return_value=iter(
                MockedResponse(
                    fixture="extras/tests/fixtures/ix_api/accounts.json"
                ).json()
            ),
        ):
            response = self.client.get(
                url,
                data={
                    "api_url": ixapi.api_url,
                    "api_key": ixapi.api_key,
                    "api_secret": ixapi.api_secret,
                },
                format="json",
                **self.header,
            )
            self.assertHttpStatus(response, status.HTTP_200_OK)


class JournalEntryTest(APIViewTestCases.View):
    model = JournalEntry
    brief_fields = ["id", "url", "display_url", "display", "created"]
    bulk_update_data = {"comments": "Overwritten"}

    @classmethod
    def setUpTestData(cls):
        user = User.objects.first()
        autonomous_system = AutonomousSystem.objects.create(name="AS 1", asn=65535)

        journal_entries = (
            JournalEntry(
                created_by=user,
                assigned_object=autonomous_system,
                comments="Fourth entry",
            ),
            JournalEntry(
                created_by=user,
                assigned_object=autonomous_system,
                comments="Fifth entry",
            ),
            JournalEntry(
                created_by=user,
                assigned_object=autonomous_system,
                comments="Sixth entry",
            ),
        )
        JournalEntry.objects.bulk_create(journal_entries)

        cls.create_data = [
            {
                "assigned_object_type": "peering.autonomoussystem",
                "assigned_object_id": autonomous_system.pk,
                "comments": "First entry",
            },
            {
                "assigned_object_type": "peering.autonomoussystem",
                "assigned_object_id": autonomous_system.pk,
                "comments": "Second entry",
            },
            {
                "assigned_object_type": "peering.autonomoussystem",
                "assigned_object_id": autonomous_system.pk,
                "comments": "Third entry",
            },
        ]


class TagTest(APIViewTestCases.View):
    model = Tag
    brief_fields = ["id", "url", "display_url", "display", "name", "slug", "color"]
    create_data = [
        {"name": "Test 4", "slug": "test-4"},
        {"name": "Test 5", "slug": "test-5"},
        {"name": "Test 6", "slug": "test-6"},
    ]
    bulk_update_data = {"color": "000000"}

    @classmethod
    def setUpTestData(cls):
        Tag.objects.bulk_create(
            [
                Tag(name="Test 1", slug="test-1", color="333333"),
                Tag(name="Test 2", slug="test-2", color="333333"),
                Tag(name="Test 3", slug="test-3", color="333333"),
            ]
        )


class WebhookTest(APIViewTestCases.View):
    model = Webhook
    brief_fields = ["id", "url", "display_url", "display", "name"]
    create_data = [
        {
            "name": "Webhook 4",
            "content_types": ["devices.router", "peering.autonomoussystem"],
            "type_create": True,
            "payload_url": "http://example.com/4",
        },
        {
            "name": "Webhook 5",
            "content_types": ["devices.router", "peering.autonomoussystem"],
            "type_update": True,
            "payload_url": "http://example.com/5",
        },
        {
            "name": "Webhook 6",
            "content_types": ["devices.router", "peering.autonomoussystem"],
            "type_delete": True,
            "payload_url": "http://example.com/6",
        },
    ]
    bulk_update_data = {"ssl_verification": False}

    @classmethod
    def setUpTestData(cls):
        as_ct = ContentType.objects.get_for_model(AutonomousSystem)
        webhooks = Webhook.objects.bulk_create(
            [
                Webhook(
                    name="Webhook 1",
                    type_create=True,
                    payload_url="http://example.com/1",
                ),
                Webhook(
                    name="Webhook 2",
                    type_update=True,
                    payload_url="http://example.com/2",
                ),
                Webhook(
                    name="Webhook 3",
                    type_delete=True,
                    payload_url="http://example.com/3",
                ),
            ]
        )
        for webhook in webhooks:
            webhook.content_types.set([as_ct])


class PrefixListViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("extras-api:api-prefix-list")

    @patch("peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen)
    def test_get_prefix_list_with_as_set(self, mocked_popen):
        response = self.client.get(
            self.url, data={"as-set": "AS-MOCKED"}, format="json", **self.header
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertIn("AS-MOCKED", response.data)
        self.assertIn("ipv4", response.data["AS-MOCKED"])
        self.assertIn("ipv6", response.data["AS-MOCKED"])
        self.assertEqual(len(response.data["AS-MOCKED"]["ipv4"]), 1)
        self.assertEqual(len(response.data["AS-MOCKED"]["ipv6"]), 1)

    @patch("peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen)
    def test_get_prefix_list_with_multiple_as_sets(self, mocked_popen):
        response = self.client.get(
            self.url, data={"as-set": "AS-MOCKED,AS65537"}, format="json", **self.header
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertIn("AS-MOCKED", response.data)
        self.assertIn("AS65537", response.data)

    @patch("peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen)
    def test_get_prefix_list_ipv4_only(self, mocked_popen):
        response = self.client.get(
            self.url,
            data={"as-set": "AS-MOCKED", "af": "4"},
            format="json",
            **self.header,
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertIn("AS-MOCKED", response.data)
        self.assertIn("ipv4", response.data["AS-MOCKED"])
        self.assertNotIn("ipv6", response.data["AS-MOCKED"])
        self.assertEqual(len(response.data["AS-MOCKED"]["ipv4"]), 1)

    @patch("peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen)
    def test_get_prefix_list_ipv6_only(self, mocked_popen):
        response = self.client.get(
            self.url,
            data={"as-set": "AS-MOCKED", "af": "6"},
            format="json",
            **self.header,
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertIn("AS-MOCKED", response.data)
        self.assertIn("ipv6", response.data["AS-MOCKED"])
        self.assertNotIn("ipv4", response.data["AS-MOCKED"])
        self.assertEqual(len(response.data["AS-MOCKED"]["ipv6"]), 1)

    def test_get_prefix_list_missing_as_set(self):
        response = self.client.get(self.url, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_get_prefix_list_invalid_af(self):
        response = self.client.get(
            self.url,
            data={"as-set": "AS-MOCKED", "af": "5"},
            format="json",
            **self.header,
        )
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    @patch("peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen)
    def test_get_prefix_list_with_cache(self, mocked_popen):
        response = self.client.get(
            self.url, data={"as-set": "AS-MOCKED"}, format="json", **self.header
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)
        call_count = mocked_popen.call_count

        cached_response = self.client.get(
            self.url, data={"as-set": "AS-MOCKED"}, format="json", **self.header
        )
        self.assertHttpStatus(cached_response, status.HTTP_200_OK)
        self.assertEqual(mocked_popen.call_count, call_count)
        self.assertEqual(response.data, cached_response.data)

    @patch("peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen)
    def test_get_prefix_list_skip_cache(self, mocked_popen):
        response = self.client.get(
            self.url,
            data={"as-set": "AS-MOCKED", "skip-cache": "true"},
            format="json",
            **self.header,
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)
        call_count = mocked_popen.call_count

        second_response = self.client.get(
            self.url,
            data={"as-set": "AS-MOCKED", "skip-cache": "true"},
            format="json",
            **self.header,
        )
        self.assertHttpStatus(second_response, status.HTTP_200_OK)
        self.assertGreater(mocked_popen.call_count, call_count)

    @patch("peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen)
    def test_get_prefix_list_no_prefixes_found(self, mocked_popen):
        response = self.client.get(
            self.url, data={"as-set": "AS-NOPREFIXES"}, format="json", **self.header
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertIn("AS-NOPREFIXES", response.data)
        self.assertEqual(len(response.data["AS-NOPREFIXES"]["ipv4"]), 0)
        self.assertEqual(len(response.data["AS-NOPREFIXES"]["ipv6"]), 0)
