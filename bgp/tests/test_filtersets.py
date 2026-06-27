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
                    category=CommunityCategory.INFORMATIONAL,
                    private=True,
                ),
                Community(
                    name="Community 2",
                    slug="community-2",
                    value="64500:2",
                    type=CommunityType.INGRESS,
                    category=CommunityCategory.ACTION,
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

    def test_category(self):
        params = {"category": [CommunityCategory.INFORMATIONAL]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"category": [CommunityCategory.ACTION]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"category": [""]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_private(self):
        params = {"private": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"private": False}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

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


class RoutingPolicyTestCase(TestCase, BaseFilterSetTests):
    queryset = RoutingPolicy.objects.all()
    filterset = RoutingPolicyFilterSet

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
                    address_family=6,
                ),
                RoutingPolicy(
                    name="Routing Policy 3",
                    slug="routing-policy-3",
                    type=RoutingPolicyType.IMPORT_EXPORT,
                    weight=10,
                ),
            ]
        )

    def test_q(self):
        params = {"q": "Routing Policy 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "routing-policy-1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_type(self):
        params = {"type": [RoutingPolicyType.IMPORT]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"type": [RoutingPolicyType.EXPORT]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"type": [RoutingPolicyType.IMPORT_EXPORT]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_weight(self):
        params = {"weight": [0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"weight": [10]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_address_family(self):
        params = {"address_family": 6}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"address_family": 4}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
