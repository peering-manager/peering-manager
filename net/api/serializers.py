from net.models import Connection
from peering.api.nested_serializers import (
    NestedInternetExchangeSerializer,
    NestedRouterSerializer,
)
from peering_manager.api import PrimaryModelSerializer

from .nested_serializers import *

__all__ = ("ConnectionSerializer", "NestedConnectionSerializer")


class ConnectionSerializer(PrimaryModelSerializer):
    name = serializers.CharField(read_only=True)
    internet_exchange_point = NestedInternetExchangeSerializer()
    router = NestedRouterSerializer()

    class Meta:
        model = Connection
        fields = [
            "id",
            "display",
            "name",
            "peeringdb_netixlan",
            "state",
            "vlan",
            "ipv6_address",
            "ipv4_address",
            "internet_exchange_point",
            "router",
            "interface",
            "description",
            "local_context_data",
            "comments",
            "tags",
        ]
