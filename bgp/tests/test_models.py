from django.test import TestCase

from bgp.models import Relationship
from utils.enums import Colour


class CommunityTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.relationships = [
            Relationship(name="Test1", slug="test1", color=Colour.YELLOW),
            Relationship(name="Test2", slug="test2", color=Colour.WHITE),
            Relationship(name="Test3", slug="test3", color=Colour.BLACK),
        ]
        Relationship.objects.bulk_create(cls.relationships)

    def test_get_html(self):
        for i in self.relationships:
            self.assertIn(i.color, i.get_html())
