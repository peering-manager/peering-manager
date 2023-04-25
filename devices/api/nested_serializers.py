from rest_framework import serializers

from devices.models import Configuration, Platform
from peering_manager.api.serializers import WritableNestedSerializer


class NestedConfigurationSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="devices-api:configuration-detail"
    )

    class Meta:
        model = Configuration
        fields = ["id", "url", "display", "name"]


class NestedPlatformSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="devices-api:platform-detail")

    class Meta:
        model = Platform
        fields = ["id", "url", "display", "name", "slug"]
