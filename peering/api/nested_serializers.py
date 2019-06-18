from rest_framework import serializers

from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    ConfigurationTemplate,
    InternetExchange,
    Router,
    RoutingPolicy,
)
from utils.api import WritableNestedSerializer


class AutonomousSystemNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="peering-api:autonomoussystem-detail"
    )

    class Meta:
        model = AutonomousSystem
        fields = ["id", "url", "asn", "name"]


class BGPGroupNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="peering-api:bgpgroup-detail")

    class Meta:
        model = BGPGroup
        fields = ["id", "url", "name", "slug"]


class CommunityNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="peering-api:community-detail")

    class Meta:
        model = Community
        fields = ["id", "url", "name", "value", "type"]


class ConfigurationTemplateNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="peering-api:configurationtemplate-detail"
    )

    class Meta:
        model = ConfigurationTemplate
        fields = ["id", "url", "name"]


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
