from rest_framework import serializers

from net.models import Connection
from peering_manager.api.serializers import WritableNestedSerializer


class NestedConnectionSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="net-api:connection-detail")

    class Meta:
        model = Connection
        fields = ["id", "url", "display", "name", "ipv6_address", "ipv4_address"]
