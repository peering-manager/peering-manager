from django.test import TestCase

from bgp.forms import RelationshipForm
from utils.enums import Color


class Relationshipest(TestCase):
    def test_relationship_form(self):
        test = RelationshipForm(
            data={
                "name": "test",
                "slug": "test",
                "color": Color.BLUE,
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())
