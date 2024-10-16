from rest_framework import serializers

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
            "display",
            "name",
            "slug",
            "description",
            "minimum_transmit_interval",
            "minimum_receive_interval",
            "detection_multiplier",
            "hold_time",
            "local_context_data",
            "tags",
            "created",
            "updated",
        ]


class NestedBFDSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="net-api:bfd-detail")

    class Meta:
        model = BFD
        fields = ["id", "url", "display", "name", "slug"]
