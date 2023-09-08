from peering_manager.api.serializers import PeeringManagerModelSerializer

from ..models import Relationship
from .nested_serializers import *

__all__ = ("RelationshipSerializer",)


class RelationshipSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = Relationship
        fields = [
            "id",
            "display",
            "name",
            "slug",
            "description",
            "color",
            "tags",
            "created",
            "updated",
        ]
