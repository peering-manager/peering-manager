from peering_manager.api.serializers import WritableNestedSerializer

from ..models import Configuration, Platform, Router

__all__ = (
    "NestedConfigurationSerializer",
    "NestedPlatformSerializer",
    "NestedRouterSerializer",
)


class NestedConfigurationSerializer(WritableNestedSerializer):
    class Meta:
        model = Configuration
        fields = ["id", "url", "display_url", "display", "name"]


class NestedPlatformSerializer(WritableNestedSerializer):
    class Meta:
        model = Platform
        fields = ["id", "url", "display", "name", "slug"]


class NestedRouterSerializer(WritableNestedSerializer):
    class Meta:
        model = Router
        fields = ["id", "url", "display_url", "display", "name", "hostname"]
