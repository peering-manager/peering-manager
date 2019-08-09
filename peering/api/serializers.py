from rest_framework.serializers import ModelSerializer
from taggit_serializer.serializers import TaggitSerializer, TagListSerializerField

from .nested_serializers import *
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
    Template,
)
from utils.api import InetAddressArrayField


class AutonomousSystemSerializer(TaggitSerializer, ModelSerializer):
    import_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    export_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    potential_internet_exchange_peering_sessions = InetAddressArrayField(read_only=True)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = AutonomousSystem
        fields = [
            "id",
            "asn",
            "name",
            "contact_name",
            "contact_phone",
            "contact_email",
            "comment",
            "irr_as_set",
            "irr_as_set_peeringdb_sync",
            "ipv6_max_prefixes",
            "ipv6_max_prefixes_peeringdb_sync",
            "ipv4_max_prefixes",
            "ipv4_max_prefixes_peeringdb_sync",
            "import_routing_policies",
            "export_routing_policies",
            "potential_internet_exchange_peering_sessions",
            "tags",
        ]


class BGPGroupSerializer(TaggitSerializer, ModelSerializer):
    import_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    export_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    communities = CommunityNestedSerializer(many=True, required=False)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = BGPGroup
        fields = [
            "id",
            "name",
            "slug",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "tags",
        ]


class CommunitySerializer(TaggitSerializer, ModelSerializer):
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Community
        fields = ["id", "name", "value", "type", "comment", "tags"]


class RouterSerializer(TaggitSerializer, ModelSerializer):
    configuration_template = TemplateNestedSerializer(required=False)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Router
        fields = [
            "id",
            "name",
            "hostname",
            "platform",
            "configuration_template",
            "comment",
            "netbox_device_id",
            "use_netbox",
            "tags",
        ]


class RoutingPolicySerializer(TaggitSerializer, ModelSerializer):
    tags = TagListSerializerField(required=False)

    class Meta:
        model = RoutingPolicy
        fields = [
            "id",
            "name",
            "slug",
            "type",
            "weight",
            "address_family",
            "comment",
            "tags",
        ]


class DirectPeeringSessionSerializer(TaggitSerializer, ModelSerializer):
    autonomous_system = AutonomousSystemNestedSerializer()
    bgp_group = BGPGroupNestedSerializer(required=False)
    import_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    export_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    router = RouterNestedSerializer(required=False)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = DirectPeeringSession
        fields = [
            "id",
            "autonomous_system",
            "local_asn",
            "local_ip_address",
            "bgp_group",
            "relationship",
            "ip_address",
            "password",
            "multihop_ttl",
            "enabled",
            "import_routing_policies",
            "export_routing_policies",
            "router",
            "bgp_state",
            "received_prefix_count",
            "advertised_prefix_count",
            "last_established_state",
            "comment",
            "tags",
        ]


class InternetExchangeSerializer(TaggitSerializer, ModelSerializer):
    configuration_template = TemplateNestedSerializer(required=False)
    import_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    export_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    communities = CommunityNestedSerializer(many=True, required=False)
    router = RouterNestedSerializer(required=False)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = InternetExchange
        fields = [
            "id",
            "peeringdb_id",
            "name",
            "slug",
            "ipv6_address",
            "ipv4_address",
            "comment",
            "configuration_template",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "router",
            "check_bgp_session_states",
            "bgp_session_states_update",
            "tags",
        ]


class InternetExchangePeeringSessionSerializer(TaggitSerializer, ModelSerializer):
    autonomous_system = AutonomousSystemNestedSerializer()
    internet_exchange = InternetExchangeNestedSerializer()
    import_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    export_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = InternetExchangePeeringSession
        fields = [
            "id",
            "autonomous_system",
            "internet_exchange",
            "ip_address",
            "password",
            "multihop_ttl",
            "enabled",
            "is_route_server",
            "import_routing_policies",
            "export_routing_policies",
            "bgp_state",
            "received_prefix_count",
            "advertised_prefix_count",
            "last_established_state",
            "comment",
            "tags",
        ]


class TemplateSerializer(TaggitSerializer, ModelSerializer):
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Template
        fields = ["id", "type", "name", "template", "comment", "tags"]
