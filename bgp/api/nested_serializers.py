from peering_manager.api.serializers import WritableNestedSerializer

from ..models import Relationship

__all__ = ("NestedRelationshipSerializer",)


class NestedRelationshipSerializer(WritableNestedSerializer):
    class Meta:
        model = Relationship
        fields = ["id", "url", "display_url", "display", "name", "slug"]
