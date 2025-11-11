from rest_framework import serializers

from peering_manager.api.serializers import (
    BaseModelSerializer,
    WritableNestedSerializer,
)

from ...models import HiddenPeer

__all__ = ("HiddenPeerSerializer", "NestedHiddenPeerSerializer")


class HiddenPeerSerializer(BaseModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = HiddenPeer
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "peeringdb_network",
            "peeringdb_ixlan",
            "until",
            "comments",
            "is_expired",
        ]


class NestedHiddenPeerSerializer(WritableNestedSerializer):
    class Meta:
        model = HiddenPeer
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "peeringdb_network",
            "peeringdb_ixlan",
            "until",
        ]
