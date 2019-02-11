from rest_framework import serializers

from peering.models import AutonomousSystem, InternetExchange
from utils.api import WritableNestedSerializer


class AutonomousSystemNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="peering-api:autonomoussystem-detail"
    )

    class Meta:
        model = AutonomousSystem
        fields = ["id", "url", "asn", "name"]


class InternetExchangeNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="peering-api:internetexchange-detail"
    )

    class Meta:
        model = InternetExchange
        fields = ["id", "url", "name", "slug"]
