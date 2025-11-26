from django.urls import reverse
from rest_framework import status

from utils.enums import Colour
from utils.testing import APITestCase, APIViewTestCases

from ..enums import CommunityType
from ..models import *


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("bgp-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CommunityTest(APIViewTestCases.View):
    model = Community
    brief_fields = [
        "id",
        "url",
        "display_url",
        "display",
        "name",
        "slug",
        "value",
        "type",
    ]
    create_data = [
        {
            "name": "Test1",
            "slug": "test1",
            "value": "64500:11",
            "type": CommunityType.EGRESS,
        },
        {
            "name": "Test2",
            "slug": "test2",
            "value": "64500:12",
            "type": CommunityType.EGRESS,
        },
        {
            "name": "Test3",
            "slug": "test3",
            "value": "64500:13",
            "type": CommunityType.INGRESS,
        },
    ]
    bulk_update_data = {"description": "New description"}

    @classmethod
    def setUpTestData(cls):
        Community.objects.bulk_create(
            [
                Community(
                    name="Test4",
                    slug="test4",
                    value="64500:4",
                    type=CommunityType.INGRESS,
                ),
                Community(
                    name="Test5",
                    slug="test5",
                    value="64500:5",
                    type=CommunityType.INGRESS,
                ),
                Community(
                    name="Test6",
                    slug="test6",
                    value="64500:6",
                    type=CommunityType.EGRESS,
                ),
            ]
        )


class RelationshipTest(APIViewTestCases.View):
    model = Relationship
    brief_fields = ["id", "url", "display_url", "display", "name", "slug"]
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
