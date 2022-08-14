from django.urls import reverse
from rest_framework import status

from bgp.models import Relationship
from utils.enums import Colour
from utils.testing import APITestCase, StandardAPITestCases


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("bgp-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RelationshipTest(StandardAPITestCases.View):
    model = Relationship
    brief_fields = ["id", "url", "display", "name", "slug"]
    create_data = [
        {"name": "Test4", "slug": "test4", "color": Colour.RED},
        {"name": "Test5", "slug": "test5", "color": Colour.GREEN},
        {"name": "Test6", "slug": "test6", "color": Colour.BLUE},
    ]
    bulk_update_data = {"description": "Foo"}

    @classmethod
    def setUpTestData(cls):
        Relationship.objects.bulk_create(
            [
                Relationship(name="Test1", slug="test1", color=Colour.YELLOW),
                Relationship(name="Test2", slug="test2", color=Colour.WHITE),
                Relationship(name="Test3", slug="test3", color=Colour.BLACK),
            ]
        )
