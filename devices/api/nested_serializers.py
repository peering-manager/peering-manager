from rest_framework import serializers

from peering_manager.api.serializers import WritableNestedSerializer

from ..models import Configuration, Platform, Router

__all__ = (
    "NestedConfigurationSerializer",
    "NestedPlatformSerializer",
    "NestedRouterSerializer",
)


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


class NestedRouterSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="devices-api:router-detail")

    class Meta:
        model = Router
        fields = ["id", "url", "display", "name", "hostname"]
