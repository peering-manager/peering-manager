from utils.enums import Colour
from utils.testing import ViewTestCases

from ..enums import CommunityType
from ..models import *


class CommunityTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Community

    @classmethod
    def setUpTestData(cls):
        Community.objects.bulk_create(
            [
                Community(name="Community 1", slug="community-1", value="64500:1"),
                Community(name="Community 2", slug="community-2", value="64500:2"),
                Community(name="Community 3", slug="community-3", value="64500:3"),
            ]
        )

        cls.form_data = {
            "name": "Community 4",
            "slug": "community-4",
            "value": "64500:4",
            "type": CommunityType.INGRESS,
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {"description": "New description"}


class RelationshipTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Relationship

    @classmethod
    def setUpTestData(cls):
        Relationship.objects.bulk_create(
            [
                Relationship(name="Test1", slug="test1", color=Colour.YELLOW),
                Relationship(name="Test2", slug="test2", color=Colour.WHITE),
                Relationship(name="Test3", slug="test3", color=Colour.BLACK),
            ]
        )

        cls.form_data = {"name": "Test4", "slug": "test4", "color": Colour.RED}
        cls.bulk_edit_data = {"description": "Foo"}
