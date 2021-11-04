from rest_framework import serializers

from devices.models import Platform
from peering_manager.api.serializers import WritableNestedSerializer


class NestedPlatformSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="devices-api:platform-detail")

    class Meta:
        model = Platform
        fields = ["id", "url", "display", "name", "slug"]
