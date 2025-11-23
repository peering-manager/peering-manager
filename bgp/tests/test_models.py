from django.forms import ValidationError
from django.test import TestCase

from utils.enums import Colour

from ..enums import *
from ..fields import *
from ..models import *


class CommunityTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.communities = [
            Community(
                name="test-1", slug="test-1", value="64500:1", type=CommunityType.EGRESS
            ),
            Community(
                name="test-2",
                slug="test-2",
                value="64500:2",
                type=CommunityType.INGRESS,
            ),
            Community(name="test-3", slug="test-3", value="64500:3", type="unknown"),
        ]
        Community.objects.bulk_create(cls.communities)

    def test_get_type_html(self):
        expected = [
            '<span class="badge text-bg-primary">Egress</span>',
            '<span class="badge text-bg-info">Ingress</span>',
            '<span class="badge text-bg-secondary">Not set</span>',
        ]

        for i in range(len(expected)):
            self.assertEqual(expected[i], self.communities[i].get_type_html())

    def test_community_validator(self):
        valid = [
            "65000:400",
            "100:200",
            "1:1",
            "target:65000:100",
            "origin:65000:200",
            "target:192.168.0.1:500",
            "65000:100:200",
            "1:0:0",
            "4294967295:4294967295:4294967295",
        ]
        for community in valid:
            try:
                validate_bgp_community(community)
            except ValidationError:
                self.fail(
                    f"validate_bgp_community raised ValidationError unexpectedly for {community}"
                )

        invalid = [
            "65000",
            "65536:100",
            "65000:65536",
            "65000:abc",
            "65000:-1",
            "target:65000:5000000000",
            "target::500",
            "target:192.168.0.1:-1",
            "65000:100:100:100",
            "65000:4294967296:0",
            "4294967296:100:100",
            "65000:100:abc",
            "65000:-1:100",
        ]
        for community in invalid:
            with self.assertRaises(
                ValidationError, msg=f"{community} should be invalid"
            ):
                validate_bgp_community(community)


class RelationshipTest(TestCase):
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
