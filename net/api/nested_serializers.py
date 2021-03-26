from rest_framework import serializers

from net.models import Connection
from utils.api import WritableNestedSerializer


class ConnectionNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="net-api:connection-detail")

    class Meta:
        model = Connection
        fields = ["id", "url", "ipv6_address", "ipv4_address"]
