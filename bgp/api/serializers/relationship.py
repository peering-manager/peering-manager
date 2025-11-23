from peering_manager.api.serializers import (
    PeeringManagerModelSerializer,
    WritableNestedSerializer,
)

from ...models import Relationship

__all__ = ("NestedRelationshipSerializer", "RelationshipSerializer")


class RelationshipSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = Relationship
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "slug",
            "description",
            "color",
            "tags",
            "created",
            "updated",
        ]


class NestedRelationshipSerializer(WritableNestedSerializer):
    class Meta:
        model = Relationship
        fields = ["id", "url", "display_url", "display", "name", "slug"]
