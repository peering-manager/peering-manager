from rest_framework import serializers

from devices.api.nested_serializers import NestedRouterSerializer
from peering.api.nested_serializers import NestedInternetExchangeSerializer
from peering_manager.api.fields import ChoiceField
from peering_manager.api.serializers import (
    PeeringManagerModelSerializer,
    WritableNestedSerializer,
)

from ...enums import ConnectionStatus
from ...models import Connection

__all__ = ("ConnectionSerializer", "NestedConnectionSerializer")


class ConnectionSerializer(PeeringManagerModelSerializer):
    name = serializers.CharField(read_only=True)
    status = ChoiceField(required=False, choices=ConnectionStatus)
    internet_exchange_point = NestedInternetExchangeSerializer(allow_null=True)
    router = NestedRouterSerializer(allow_null=True)

    class Meta:
        model = Connection
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "peeringdb_netixlan",
            "status",
            "vlan",
            "mac_address",
            "ipv6_address",
            "ipv4_address",
            "internet_exchange_point",
            "router",
            "interface",
            "description",
            "local_context_data",
            "config_context",
            "comments",
            "tags",
            "created",
            "updated",
        ]


class NestedConnectionSerializer(WritableNestedSerializer):
    name = serializers.CharField(read_only=True)

    class Meta:
        model = Connection
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "mac_address",
            "ipv6_address",
            "ipv4_address",
        ]
