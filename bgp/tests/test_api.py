from django.urls import reverse
from rest_framework import status

from bgp.models import Relationship
from utils.enums import Color
from utils.testing import APITestCase, StandardAPITestCases


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("bgp-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RelationshipTest(StandardAPITestCases.View):
    model = Relationship
    brief_fields = ["id", "url", "display", "name", "slug"]
    create_data = [
        {"name": "Test4", "slug": "test4", "color": Color.RED},
        {"name": "Test5", "slug": "test5", "color": Color.GREEN},
        {"name": "Test6", "slug": "test6", "color": Color.BLUE},
    ]
    bulk_update_data = {"description": "Foo"}

    @classmethod
    def setUpTestData(cls):
        Relationship.objects.bulk_create(
            [
                Relationship(name="Test1", slug="test1", color=Color.YELLOW),
                Relationship(name="Test2", slug="test2", color=Color.WHITE),
                Relationship(name="Test3", slug="test3", color=Color.BLACK),
            ]
        )
