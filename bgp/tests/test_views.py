from utils.enums import Colour
from utils.testing import ViewTestCases

from ..enums import CommunityType, RoutingPolicyType
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


class RoutingPolicyTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = RoutingPolicy

    @classmethod
    def setUpTestData(cls):
        RoutingPolicy.objects.bulk_create(
            [
                RoutingPolicy(
                    name="Routing Policy 1",
                    slug="routing-policy-1",
                    type=RoutingPolicyType.EXPORT,
                    weight=0,
                ),
                RoutingPolicy(
                    name="Routing Policy 2",
                    slug="routing-policy-2",
                    type=RoutingPolicyType.IMPORT,
                    weight=0,
                ),
                RoutingPolicy(
                    name="Routing Policy 3",
                    slug="routing-policy-3",
                    type=RoutingPolicyType.IMPORT_EXPORT,
                    weight=0,
                ),
            ]
        )

        cls.form_data = {
            "name": "Routing Policy 4",
            "slug": "routing-policy-4",
            "type": RoutingPolicyType.IMPORT,
            "address_family": 6,
            "weight": 1,
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {"weight": 10, "description": "New description"}
