from django.test import TestCase

from bgp.forms import RelationshipForm
from utils.enums import Colour


class Relationshipest(TestCase):
    def test_relationship_form(self):
        test = RelationshipForm(
            data={"name": "test", "slug": "test", "color": Colour.BLUE}
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())
