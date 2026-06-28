from peering_manager.api.fields import SerializedPKRelatedField
from peering_manager.api.serializers import (
    PeeringManagerModelSerializer,
    WritableNestedSerializer,
)

from ...models import Community, RoutingPolicy
from .community import NestedCommunitySerializer

__all__ = ("NestedRoutingPolicySerializer", "RoutingPolicySerializer")


class RoutingPolicySerializer(PeeringManagerModelSerializer):
    communities = SerializedPKRelatedField(
        queryset=Community.objects.all(),
        serializer=NestedCommunitySerializer,
        required=False,
        many=True,
    )

    class Meta:
        model = RoutingPolicy
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "slug",
            "description",
            "type",
            "weight",
            "address_family",
            "communities",
            "local_context_data",
            "config_context",
            "tags",
            "created",
            "updated",
        ]


class NestedRoutingPolicySerializer(WritableNestedSerializer):
    class Meta:
        model = RoutingPolicy
        fields = ["id", "url", "display_url", "display", "name", "slug", "type"]
