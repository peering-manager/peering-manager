from rest_framework import serializers

from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    Configuration,
    DirectPeeringSession,
    Email,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from peering_manager.api.serializers import WritableNestedSerializer


class NestedAutonomousSystemSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="peering-api:autonomoussystem-detail"
    )

    class Meta:
        model = AutonomousSystem
        fields = [
            "id",
            "url",
            "display",
            "asn",
            "name",
            "ipv6_max_prefixes",
            "ipv4_max_prefixes",
        ]


class NestedBGPGroupSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="peering-api:bgpgroup-detail")

    class Meta:
        model = BGPGroup
        fields = ["id", "url", "display", "name", "slug"]


class NestedCommunitySerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="peering-api:community-detail")

    class Meta:
        model = Community
        fields = ["id", "url", "display", "name", "slug", "value", "type"]


class NestedConfigurationSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="peering-api:configuration-detail"
    )

    class Meta:
        model = Configuration
        fields = ["id", "url", "display", "name"]


class NestedDirectPeeringSessionSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="peering-api:directpeeringsession-detail"
    )

    class Meta:
        model = DirectPeeringSession
        fields = ["id", "url", "display", "ip_address", "enabled"]


class NestedEmailSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="peering-api:email-detail")

    class Meta:
        model = Email
        fields = ["id", "url", "display", "name"]


class NestedInternetExchangeSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="peering-api:internetexchange-detail"
    )

    class Meta:
        model = InternetExchange
        fields = ["id", "url", "display", "name", "slug"]


class NestedInternetExchangePeeringSessionSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="peering-api:internetexchangepeeringsession-detail"
    )

    class Meta:
        model = InternetExchangePeeringSession
        fields = [
            "id",
            "url",
            "display",
            "ip_address",
            "enabled",
            "is_route_server",
        ]


class NestedRouterSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="peering-api:router-detail")

    class Meta:
        model = Router
        fields = ["id", "url", "display", "name", "hostname"]


class NestedRoutingPolicySerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="peering-api:routingpolicy-detail"
    )

    class Meta:
        model = RoutingPolicy
        fields = ["id", "url", "display", "name", "slug", "type"]
