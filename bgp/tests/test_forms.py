from django.test import TestCase

from utils.enums import Colour

from ..enums import *
from ..forms import *


class CommunityTest(TestCase):
    def test_community_form(self):
        test = CommunityForm(
            data={
                "name": "test",
                "slug": "test",
                "value": "64500:1",
                "type": CommunityType.EGRESS,
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())


class Relationshipest(TestCase):
    def test_relationship_form(self):
        test = RelationshipForm(
            data={"name": "test", "slug": "test", "color": Colour.BLUE}
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())
