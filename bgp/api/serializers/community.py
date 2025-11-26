from peering_manager.api.serializers import (
    PeeringManagerModelSerializer,
    WritableNestedSerializer,
)

from ...models import Community

__all__ = ("CommunitySerializer", "NestedCommunitySerializer")


class CommunitySerializer(PeeringManagerModelSerializer):
    class Meta:
        model = Community
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "slug",
            "description",
            "value",
            "type",
            "kind",
            "local_context_data",
            "config_context",
            "tags",
            "created",
            "updated",
        ]


class NestedCommunitySerializer(WritableNestedSerializer):
    class Meta:
        model = Community
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "slug",
            "value",
            "type",
        ]
