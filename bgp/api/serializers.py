from bgp.models import Relationship
from peering_manager.api.serializers import ValidatedModelSerializer

from .nested_serializers import *

__all__ = ("RelationshipSerializer", "NestedRelationshipSerializer")


class RelationshipSerializer(ValidatedModelSerializer):
    class Meta:
        model = Relationship
        fields = ["id", "display", "name", "slug", "description", "color"]
