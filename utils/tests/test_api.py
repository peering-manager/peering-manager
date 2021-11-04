from django.urls import reverse
from rest_framework import status

from utils.models import Tag
from utils.testing import APITestCase, StandardAPITestCases


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("utils-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TagTest(StandardAPITestCases.View):
    model = Tag
    brief_fields = ["id", "url", "name", "slug", "color"]
    create_data = [
        {
            "name": "Test 4",
            "slug": "test-4",
        },
        {
            "name": "Test 5",
            "slug": "test-5",
        },
        {
            "name": "Test 6",
            "slug": "test-6",
        },
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
