from rest_framework import serializers

from bgp.models import Relationship
from peering_manager.api.serializers import WritableNestedSerializer


class NestedRelationshipSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="bgp-api:relationship-detail")

    class Meta:
        model = Relationship
        fields = ["id", "url", "display", "name", "slug"]
