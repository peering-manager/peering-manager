from rest_framework import serializers

from bgp.api.serializers import NestedRelationshipSerializer
from devices.api.serializers import (
    NestedConfigurationSerializer,
    NestedPlatformSerializer,
)
from extras.api.serializers import NestedIXAPISerializer
from net.api.serializers import NestedConnectionSerializer
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from peering_manager.api import PrimaryModelSerializer, SerializedPKRelatedField

from .nested_serializers import *

__all__ = (
    "AutonomousSystemSerializer",
    "AutonomousSystemGenerateEmailSerializer",
    "BGPGroupSerializer",
    "CommunitySerializer",
    "DirectPeeringSessionSerializer",
    "InternetExchangeSerializer",
    "InternetExchangePeeringSessionSerializer",
    "RouterSerializer",
    "RouterConfigureSerializer",
    "RoutingPolicySerializer",
    "NestedAutonomousSystemSerializer",
    "NestedBGPGroupSerializer",
    "NestedCommunitySerializer",
    "NestedDirectPeeringSessionSerializer",
    "NestedInternetExchangeSerializer",
    "NestedInternetExchangePeeringSessionSerializer",
    "NestedRouterSerializer",
    "NestedRoutingPolicySerializer",
)


class AutonomousSystemSerializer(PrimaryModelSerializer):
    import_routing_policies = SerializedPKRelatedField(
        queryset=RoutingPolicy.objects.all(),
        serializer=NestedRoutingPolicySerializer,
        required=False,
        many=True,
    )
    export_routing_policies = SerializedPKRelatedField(
        queryset=RoutingPolicy.objects.all(),
        serializer=NestedRoutingPolicySerializer,
        required=False,
        many=True,
    )
    communities = SerializedPKRelatedField(
        queryset=Community.objects.all(),
        serializer=NestedCommunitySerializer,
        required=False,
        many=True,
    )

    class Meta:
        model = AutonomousSystem
        fields = [
            "id",
            "display",
            "asn",
            "name",
            "comments",
            "irr_as_set",
            "irr_as_set_peeringdb_sync",
            "ipv6_max_prefixes",
            "ipv6_max_prefixes_peeringdb_sync",
            "ipv4_max_prefixes",
            "ipv4_max_prefixes_peeringdb_sync",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "prefixes",
            "affiliated",
            "tags",
        ]


class AutonomousSystemGenerateEmailSerializer(serializers.Serializer):
    email = serializers.IntegerField()


class BGPGroupSerializer(PrimaryModelSerializer):
    import_routing_policies = SerializedPKRelatedField(
        queryset=RoutingPolicy.objects.all(),
        serializer=NestedRoutingPolicySerializer,
        required=False,
        many=True,
    )
    export_routing_policies = SerializedPKRelatedField(
        queryset=RoutingPolicy.objects.all(),
        serializer=NestedRoutingPolicySerializer,
        required=False,
        many=True,
    )
    communities = SerializedPKRelatedField(
        queryset=Community.objects.all(),
        serializer=NestedCommunitySerializer,
        required=False,
        many=True,
    )

    class Meta:
        model = BGPGroup
        fields = [
            "id",
            "display",
            "name",
            "slug",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "comments",
            "tags",
        ]


class CommunitySerializer(PrimaryModelSerializer):
    class Meta:
        model = Community
        fields = ["id", "display", "name", "slug", "value", "type", "comments", "tags"]


class DirectPeeringSessionSerializer(PrimaryModelSerializer):
    local_autonomous_system = NestedAutonomousSystemSerializer()
    autonomous_system = NestedAutonomousSystemSerializer()
    bgp_group = NestedBGPGroupSerializer(required=False)
    relationship = NestedRelationshipSerializer()
    import_routing_policies = SerializedPKRelatedField(
        queryset=RoutingPolicy.objects.all(),
        serializer=NestedRoutingPolicySerializer,
        required=False,
        many=True,
    )
    export_routing_policies = SerializedPKRelatedField(
        queryset=RoutingPolicy.objects.all(),
        serializer=NestedRoutingPolicySerializer,
        required=False,
        many=True,
    )
    router = NestedRouterSerializer(required=False)

    class Meta:
        model = DirectPeeringSession
        fields = [
            "id",
            "display",
            "service_reference",
            "local_autonomous_system",
            "local_ip_address",
            "autonomous_system",
            "bgp_group",
            "relationship",
            "ip_address",
            "password",
            "encrypted_password",
            "multihop_ttl",
            "enabled",
            "import_routing_policies",
            "export_routing_policies",
            "router",
            "bgp_state",
            "received_prefix_count",
            "advertised_prefix_count",
            "last_established_state",
            "comments",
            "tags",
        ]

    def validate(self, attrs):
        multihop_ttl = attrs.get("multihop_ttl")
        ip_src = attrs.get("local_ip_address")
        ip_dst = attrs.get("ip_address")

        if multihop_ttl == 1 and ip_src and (ip_src.network != ip_dst.network):
            raise serializers.ValidationError(
                f"{ip_src} and {ip_dst} don't belong to the same subnet."
            )

        return super().validate(attrs)


class InternetExchangeSerializer(PrimaryModelSerializer):
    ixapi_endpoint = NestedIXAPISerializer(required=False)
    local_autonomous_system = NestedAutonomousSystemSerializer()
    import_routing_policies = SerializedPKRelatedField(
        queryset=RoutingPolicy.objects.all(),
        serializer=NestedRoutingPolicySerializer,
        required=False,
        many=True,
    )
    export_routing_policies = SerializedPKRelatedField(
        queryset=RoutingPolicy.objects.all(),
        serializer=NestedRoutingPolicySerializer,
        required=False,
        many=True,
    )
    communities = SerializedPKRelatedField(
        queryset=Community.objects.all(),
        serializer=NestedCommunitySerializer,
        required=False,
        many=True,
    )

    class Meta:
        model = InternetExchange
        fields = [
            "id",
            "display",
            "peeringdb_ixlan",
            "ixapi_endpoint",
            "local_autonomous_system",
            "name",
            "slug",
            "comments",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "tags",
        ]


class InternetExchangePeeringSessionSerializer(PrimaryModelSerializer):
    autonomous_system = NestedAutonomousSystemSerializer()
    ixp_connection = NestedConnectionSerializer()
    import_routing_policies = SerializedPKRelatedField(
        queryset=RoutingPolicy.objects.all(),
        serializer=NestedRoutingPolicySerializer,
        required=False,
        many=True,
    )
    export_routing_policies = SerializedPKRelatedField(
        queryset=RoutingPolicy.objects.all(),
        serializer=NestedRoutingPolicySerializer,
        required=False,
        many=True,
    )

    class Meta:
        model = InternetExchangePeeringSession
        fields = [
            "id",
            "display",
            "service_reference",
            "autonomous_system",
            "ixp_connection",
            "ip_address",
            "password",
            "encrypted_password",
            "multihop_ttl",
            "enabled",
            "is_route_server",
            "import_routing_policies",
            "export_routing_policies",
            "bgp_state",
            "received_prefix_count",
            "advertised_prefix_count",
            "last_established_state",
            "comments",
            "tags",
        ]


class RouterSerializer(PrimaryModelSerializer):
    poll_bgp_sessions_last_updated = serializers.DateTimeField(read_only=True)
    configuration_template = NestedConfigurationSerializer(required=False)
    local_autonomous_system = NestedAutonomousSystemSerializer()
    platform = NestedPlatformSerializer()

    class Meta:
        model = Router
        fields = [
            "id",
            "display",
            "name",
            "hostname",
            "platform",
            "encrypt_passwords",
            "poll_bgp_sessions_state",
            "poll_bgp_sessions_last_updated",
            "configuration_template",
            "local_autonomous_system",
            "netbox_device_id",
            "device_state",
            "use_netbox",
            "config_context",
            "napalm_username",
            "napalm_password",
            "napalm_timeout",
            "napalm_args",
            "comments",
            "tags",
        ]


class RouterConfigureSerializer(serializers.Serializer):
    routers = serializers.ListField(child=serializers.IntegerField())
    commit = serializers.BooleanField()


class RoutingPolicySerializer(PrimaryModelSerializer):
    class Meta:
        model = RoutingPolicy
        fields = [
            "id",
            "display",
            "name",
            "slug",
            "type",
            "weight",
            "address_family",
            "config_context",
            "comments",
            "tags",
        ]
