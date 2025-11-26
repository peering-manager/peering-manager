from django.test import TestCase

from utils.enums import Colour
from utils.testing import BaseFilterSetTests

from ..enums import *
from ..filtersets import *
from ..models import *


class CommunityTestCase(TestCase, BaseFilterSetTests):
    queryset = Community.objects.all()
    filterset = CommunityFilterSet

    @classmethod
    def setUpTestData(cls):
        Community.objects.bulk_create(
            [
                Community(
                    name="Community 1",
                    slug="community-1",
                    value="64500:1",
                    type=CommunityType.EGRESS,
                ),
                Community(
                    name="Community 2",
                    slug="community-2",
                    value="64500:2",
                    type=CommunityType.INGRESS,
                ),
                Community(name="Community 3", slug="community-3", value="64500:3"),
            ]
        )

    def test_q(self):
        params = {"q": "Community 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "community-1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_type(self):
        params = {"type": [""]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"type": [CommunityType.INGRESS]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"type": [CommunityType.EGRESS]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_value(self):
        params = {"value": ["64500:1"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class RelationshipTestCase(TestCase, BaseFilterSetTests):
    queryset = Relationship.objects.all()
    filterset = RelationshipFilterSet

    @classmethod
    def setUpTestData(cls):
        Relationship.objects.bulk_create(
            [
                Relationship(name="Test1", slug="test1", color=Colour.YELLOW),
                Relationship(name="Test2", slug="test2", color=Colour.WHITE),
                Relationship(name="Test3", slug="test3", color=Colour.BLACK),
            ]
        )

    def test_q(self):
        params = {"q": "test1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "test2"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "test"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
