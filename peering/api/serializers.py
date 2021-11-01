from rest_framework import serializers

from devices.api.nested_serializers import NestedPlatformSerializer
from net.api.serializers import NestedConnectionSerializer
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
from peering_manager.api.fields import SerializedPKRelatedField
from peering_manager.api.serializers import PrimaryModelSerializer

from .nested_serializers import *

__all__ = (
    "AutonomousSystemSerializer",
    "BGPGroupSerializer",
    "CommunitySerializer",
    "ConfigurationSerializer",
    "DirectPeeringSessionSerializer",
    "EmailSerializer",
    "InternetExchangeSerializer",
    "InternetExchangePeeringSessionSerializer",
    "RouterSerializer",
    "RoutingPolicySerializer",
    "NestedAutonomousSystemSerializer",
    "NestedBGPGroupSerializer",
    "NestedCommunitySerializer",
    "NestedConfigurationSerializer",
    "NestedDirectPeeringSessionSerializer",
    "NestedEmailSerializer",
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
            "contact_name",
            "contact_phone",
            "contact_email",
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


class AutonomousGenerateEmailSerializer(serializers.Serializer):
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


class ConfigurationSerializer(PrimaryModelSerializer):
    class Meta:
        model = Configuration
        fields = [
            "id",
            "display",
            "name",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
            "comments",
            "tags",
        ]


class DirectPeeringSessionSerializer(PrimaryModelSerializer):
    local_autonomous_system = NestedAutonomousSystemSerializer()
    autonomous_system = NestedAutonomousSystemSerializer()
    bgp_group = NestedBGPGroupSerializer(required=False)
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


class EmailSerializer(PrimaryModelSerializer):
    class Meta:
        model = Email
        fields = [
            "id",
            "display",
            "name",
            "subject",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
            "comments",
            "tags",
        ]


class InternetExchangeSerializer(PrimaryModelSerializer):
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
            "local_autonomous_system",
            "name",
            "slug",
            "comments",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "check_bgp_session_states",
            "bgp_session_states_update",
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
