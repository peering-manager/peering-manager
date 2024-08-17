from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from bgp.api.serializers import NestedRelationshipSerializer
from devices.api.serializers import NestedRouterSerializer
from extras.api.serializers import NestedIXAPISerializer
from net.api.serializers import NestedConnectionSerializer
from peering_manager.api.fields import ChoiceField, SerializedPKRelatedField
from peering_manager.api.serializers import PeeringManagerModelSerializer

from ..enums import BGPGroupStatus, BGPSessionStatus
from ..models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)
from .nested_serializers import *

__all__ = (
    "AutonomousSystemSerializer",
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
    "NestedRoutingPolicySerializer",
)


class AutonomousSystemSerializer(PeeringManagerModelSerializer):
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
            "description",
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
            "local_context_data",
            "tags",
            "created",
            "updated",
        ]


class BGPGroupSerializer(PeeringManagerModelSerializer):
    status = ChoiceField(required=False, choices=BGPGroupStatus)
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
            "description",
            "status",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "local_context_data",
            "tags",
            "created",
            "updated",
        ]


class CommunitySerializer(PeeringManagerModelSerializer):
    class Meta:
        model = Community
        fields = [
            "id",
            "display",
            "name",
            "slug",
            "description",
            "value",
            "type",
            "local_context_data",
            "tags",
            "created",
            "updated",
        ]


class DirectPeeringSessionSerializer(PeeringManagerModelSerializer):
    local_autonomous_system = NestedAutonomousSystemSerializer()
    autonomous_system = NestedAutonomousSystemSerializer()
    bgp_group = NestedBGPGroupSerializer(required=False, allow_null=True)
    status = ChoiceField(required=False, choices=BGPSessionStatus)
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
    communities = SerializedPKRelatedField(
        queryset=Community.objects.all(),
        serializer=NestedCommunitySerializer,
        required=False,
        many=True,
    )
    router = NestedRouterSerializer(required=False, allow_null=True)

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
            "ip_address",
            "status",
            "relationship",
            "password",
            "encrypted_password",
            "multihop_ttl",
            "passive",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "router",
            "local_context_data",
            "bgp_state",
            "received_prefix_count",
            "accepted_prefix_count",
            "advertised_prefix_count",
            "last_established_state",
            "comments",
            "tags",
            "created",
            "updated",
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


class InternetExchangeSerializer(PeeringManagerModelSerializer):
    ixapi_endpoint = NestedIXAPISerializer(required=False, allow_null=True)
    peeringdb_prefixes = serializers.DictField(read_only=True)
    local_autonomous_system = NestedAutonomousSystemSerializer()
    status = ChoiceField(required=False, choices=BGPGroupStatus)
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
            "peeringdb_prefixes",
            "ixapi_endpoint",
            "name",
            "slug",
            "description",
            "status",
            "local_autonomous_system",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "local_context_data",
            "tags",
            "created",
            "updated",
        ]

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_peeringdb_prefixes(self, object):
        return object.peeringdb_prefixes


class InternetExchangePeeringSessionSerializer(PeeringManagerModelSerializer):
    autonomous_system = NestedAutonomousSystemSerializer()
    ixp_connection = NestedConnectionSerializer()
    status = ChoiceField(required=False, choices=BGPSessionStatus)
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
    exists_in_peeringdb = serializers.BooleanField(read_only=True)
    is_abandoned = serializers.BooleanField(read_only=True)

    class Meta:
        model = InternetExchangePeeringSession
        fields = [
            "id",
            "display",
            "service_reference",
            "autonomous_system",
            "ixp_connection",
            "ip_address",
            "status",
            "password",
            "encrypted_password",
            "multihop_ttl",
            "passive",
            "is_route_server",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "local_context_data",
            "exists_in_peeringdb",
            "is_abandoned",
            "bgp_state",
            "received_prefix_count",
            "accepted_prefix_count",
            "advertised_prefix_count",
            "last_established_state",
            "comments",
            "tags",
            "created",
            "updated",
        ]


class RoutingPolicySerializer(PeeringManagerModelSerializer):
    communities = SerializedPKRelatedField(
        queryset=Community.objects.all(),
        serializer=NestedCommunitySerializer,
        required=False,
        many=True,
    )

    class Meta:
        model = RoutingPolicy
        fields = [
            "id",
            "display",
            "name",
            "slug",
            "description",
            "type",
            "weight",
            "address_family",
            "communities",
            "local_context_data",
            "tags",
            "created",
            "updated",
        ]
