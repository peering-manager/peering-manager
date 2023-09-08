from rest_framework import serializers

from peering_manager.api.serializers import WritableNestedSerializer

from ..models import Relationship

__all__ = ("NestedRelationshipSerializer",)


class NestedRelationshipSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="bgp-api:relationship-detail")

    class Meta:
        model = Relationship
        fields = ["id", "url", "display", "name", "slug"]
