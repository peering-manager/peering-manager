from django.test import TestCase

from bgp.filters import RelationshipFilterSet
from bgp.models import Relationship
from utils.enums import Color
from utils.testing import BaseFilterSetTests


class RelationshipTestCase(TestCase, BaseFilterSetTests):
    queryset = Relationship.objects.all()
    filterset = RelationshipFilterSet

    @classmethod
    def setUpTestData(cls):
        Relationship.objects.bulk_create(
            [
                Relationship(name="Test1", slug="test1", color=Color.YELLOW),
                Relationship(name="Test2", slug="test2", color=Color.WHITE),
                Relationship(name="Test3", slug="test3", color=Color.BLACK),
            ]
        )

    def test_q(self):
        params = {"q": "test1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "test2"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "test"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
