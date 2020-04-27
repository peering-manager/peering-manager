from rest_framework import serializers

from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    InternetExchange,
    Router,
    RoutingPolicy,
    Template,
)
from utils.api import WritableNestedSerializer


class AutonomousSystemNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="peering-api:autonomoussystem-detail"
    )

    class Meta:
        model = AutonomousSystem
        fields = ["id", "url", "asn", "name", "ipv6_max_prefixes", "ipv4_max_prefixes"]


class BGPGroupNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="peering-api:bgpgroup-detail")

    class Meta:
        model = BGPGroup
        fields = ["id", "url", "name", "slug"]


class CommunityNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="peering-api:community-detail")

    class Meta:
        model = Community
        fields = ["id", "url", "name", "description", "value", "type"]


class InternetExchangeNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="peering-api:internetexchange-detail"
    )

    class Meta:
        model = InternetExchange
        fields = ["id", "url", "name", "slug"]


class RouterNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="peering-api:router-detail")

    class Meta:
        model = Router
        fields = ["id", "url", "name", "hostname", "platform"]


class RoutingPolicyNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="peering-api:routingpolicy-detail"
    )

    class Meta:
        model = RoutingPolicy
        fields = ["id", "url", "name", "slug", "type"]


class TemplateNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="peering-api:template-detail")

    class Meta:
        model = Template
        fields = ["id", "url", "type", "name"]
