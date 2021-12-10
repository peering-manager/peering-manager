from django.test import TestCase

from bgp.models import Relationship
from utils.enums import Color


class CommunityTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.relationships = [
            Relationship(name="Test1", slug="test1", color=Color.YELLOW),
            Relationship(name="Test2", slug="test2", color=Color.WHITE),
            Relationship(name="Test3", slug="test3", color=Color.BLACK),
        ]
        Relationship.objects.bulk_create(cls.relationships)

    def test_get_html(self):
        for i in self.relationships:
            self.assertIn(i.color, i.get_html())
