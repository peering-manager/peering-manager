from peering_manager.api.serializers import (
    PeeringManagerModelSerializer,
    WritableNestedSerializer,
)

from ...models import BFD

__all__ = ("BFDSerializer", "NestedBFDSerializer")


class BFDSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = BFD
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "slug",
            "description",
            "minimum_transmit_interval",
            "minimum_receive_interval",
            "detection_multiplier",
            "hold_time",
            "local_context_data",
            "config_context",
            "tags",
            "created",
            "updated",
        ]


class NestedBFDSerializer(WritableNestedSerializer):
    class Meta:
        model = BFD
        fields = ["id", "url", "display_url", "display", "name", "slug"]
