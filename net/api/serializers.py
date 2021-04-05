from rest_framework.serializers import ModelSerializer

from net.models import Connection
from peering.api.nested_serializers import (
    InternetExchangeNestedSerializer,
    RouterNestedSerializer,
)
from utils.api.serializers import TaggedObjectSerializer

from .nested_serializers import *


class ConnectionSerializer(TaggedObjectSerializer, ModelSerializer):
    internet_exchange_point = InternetExchangeNestedSerializer()
    router = RouterNestedSerializer()

    class Meta:
        model = Connection
        fields = [
            "id",
            "name",
            "peeringdb_netixlan",
            "state",
            "vlan",
            "ipv6_address",
            "ipv4_address",
            "internet_exchange_point",
            "router",
            "description",
            "comments",
            "tags",
        ]
