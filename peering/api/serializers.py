from __future__ import annotations

from typing import TYPE_CHECKING

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from bgp.api.serializers import NestedCommunitySerializer, NestedRelationshipSerializer
from bgp.models import Community
from devices.api.serializers import NestedRouterSerializer
from extras.api.serializers import NestedIXAPISerializer
from net.api.serializers import NestedBFDSerializer, NestedConnectionSerializer
from peering_manager.api.fields import ChoiceField, SerializedPKRelatedField
from peering_manager.api.serializers import PeeringManagerModelSerializer

from ..enums import (
    BGPGroupStatus,
    BGPSessionStatus,
    IPFamily,
    PeeringRequestStatus,
    PeeringRequestType,
    RequestedSessionStatus,
)
from ..models import (
    AutonomousSystem,
    BGPGroup,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    PeeringRequest,
    RequestedSession,
    RoutingPolicy,
)
from .nested_serializers import *

if TYPE_CHECKING:
    from ipaddress import IPv4Interface, IPv6Interface

__all__ = (
    "AutonomousSystemSerializer",
    "BGPGroupSerializer",
    "DirectPeeringSessionSerializer",
    "InternetExchangePeeringSessionSerializer",
    "InternetExchangeSerializer",
    "NestedAutonomousSystemSerializer",
    "NestedBGPGroupSerializer",
    "NestedDirectPeeringSessionSerializer",
    "NestedInternetExchangePeeringSessionSerializer",
    "NestedInternetExchangeSerializer",
    "NestedPeeringRequestSerializer",
    "NestedRequestedSessionSerializer",
    "NestedRoutingPolicySerializer",
    "PeeringRequestSerializer",
    "RequestedSessionSerializer",
    "RouterConfigureSerializer",
    "RouterSerializer",
    "RoutingPolicySerializer",
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
            "url",
            "display_url",
            "display",
            "asn",
            "name",
            "name_peeringdb_sync",
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
            "retrieve_prefixes",
            "as_list",
            "retrieve_as_list",
            "irr_sources_override",
            "irr_ipv6_prefixes_args_override",
            "irr_ipv4_prefixes_args_override",
            "affiliated",
            "local_context_data",
            "config_context",
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
            "url",
            "display_url",
            "display",
            "name",
            "slug",
            "description",
            "status",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "local_context_data",
            "config_context",
            "tags",
            "created",
            "updated",
        ]


class CommunitySerializer(PeeringManagerModelSerializer):
    class Meta:
        model = Community
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "slug",
            "description",
            "value",
            "type",
            "kind",
            "local_context_data",
            "config_context",
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
    bfd = NestedBFDSerializer(required=False, allow_null=True)
    router = NestedRouterSerializer(required=False, allow_null=True)
    connection = NestedConnectionSerializer(required=False, allow_null=True)

    class Meta:
        model = DirectPeeringSession
        fields = [
            "id",
            "url",
            "display_url",
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
            "bfd",
            "router",
            "connection",
            "local_context_data",
            "config_context",
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

    def validate(self, data):
        # Invalid IP address, let the field validator handle it
        if "ip_address" not in data:
            return super().validate(data)

        ip_dst: IPv6Interface | IPv4Interface = data["ip_address"]
        policies: list[RoutingPolicy] = []
        if "import_routing_policies" in data:
            policies += data["import_routing_policies"]
        if "export_routing_policies" in data:
            policies += data["export_routing_policies"]

        # Make sure that routing policies are compatible (address family)
        for policy in policies:
            if policy.address_family not in (IPFamily.ALL, ip_dst.version):
                raise serializers.ValidationError(
                    f"Routing policy '{policy.name}' cannot be used for this session, address families mismatch."
                )

        return super().validate(data)


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
            "url",
            "display_url",
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
            "config_context",
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
    bfd = NestedBFDSerializer(required=False, allow_null=True)
    exists_in_peeringdb = serializers.BooleanField(read_only=True)
    is_abandoned = serializers.BooleanField(read_only=True)

    class Meta:
        model = InternetExchangePeeringSession
        fields = [
            "id",
            "url",
            "display_url",
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
            "bfd",
            "local_context_data",
            "config_context",
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


class RequestedSessionSerializer(PeeringManagerModelSerializer):
    peering_request = NestedPeeringRequestSerializer(read_only=True)
    address_family = serializers.IntegerField(read_only=True)
    status = ChoiceField(read_only=True, choices=RequestedSessionStatus)

    class Meta:
        model = RequestedSession
        fields = [
            "id",
            "url",
            "display",
            "peering_request",
            "internet_exchange",
            "peeringdb_facility",
            "ip_address",
            "address_family",
            "session_secret",
            "status",
            "rejection_comment",
            "created_session_type",
            "created_session_id",
            "created",
            "updated",
        ]


class PeeringRequestSerializer(PeeringManagerModelSerializer):
    local_autonomous_system = NestedAutonomousSystemSerializer()
    request_type = ChoiceField(required=False, choices=PeeringRequestType)
    status = ChoiceField(read_only=True, choices=PeeringRequestStatus)
    relationship = NestedRelationshipSerializer(required=False, allow_null=True)
    requested_sessions = RequestedSessionSerializer(many=True, read_only=True)

    class Meta:
        model = PeeringRequest
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "tracking_id",
            "requesting_asn",
            "requester_email",
            "local_autonomous_system",
            "request_type",
            "status",
            "decision_comment",
            "relationship",
            "requested_sessions",
            "description",
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
            "url",
            "display_url",
            "display",
            "name",
            "slug",
            "description",
            "type",
            "weight",
            "address_family",
            "communities",
            "local_context_data",
            "config_context",
            "tags",
            "created",
            "updated",
        ]
