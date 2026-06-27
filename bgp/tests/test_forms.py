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

        test = CommunityForm(
            data={
                "name": "test-cat",
                "slug": "test-cat",
                "value": "64500:2",
                "category": CommunityCategory.ACTION,
            }
        )
        self.assertTrue(test.is_valid())
        test.save()


class Relationshipest(TestCase):
    def test_relationship_form(self):
        test = RelationshipForm(
            data={"name": "test", "slug": "test", "color": Colour.BLUE}
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())


class RoutingPolicyTest(TestCase):
    def test_routing_policy_form(self):
        test = RoutingPolicyForm(
            data={
                "name": "Test",
                "slug": "test",
                "type": RoutingPolicyType.IMPORT,
                "weight": 0,
                "address_family": 0,
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())
