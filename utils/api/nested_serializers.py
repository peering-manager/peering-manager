from rest_framework import serializers

from peering_manager.api.serializers import WritableNestedSerializer
from utils.models import Tag


class NestedTagSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="utils-api:tag-detail")

    class Meta:
        model = Tag
        fields = ["id", "url", "name", "slug", "color"]
