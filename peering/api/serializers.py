from rest_framework.serializers import ModelSerializer
from taggit_serializer.serializers import TaggitSerializer, TagListSerializerField

from .nested_serializers import *
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
from utils.api import InetAddressArrayField, WriteEnabledNestedSerializer


class AutonomousSystemSerializer(TaggitSerializer, WriteEnabledNestedSerializer):
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
            "comments",
            "irr_as_set",
            "irr_as_set_peeringdb_sync",
            "ipv6_max_prefixes",
            "ipv6_max_prefixes_peeringdb_sync",
            "ipv4_max_prefixes",
            "ipv4_max_prefixes_peeringdb_sync",
            "import_routing_policies",
            "export_routing_policies",
            "potential_internet_exchange_peering_sessions",
            "prefixes",
            "affiliated",
            "tags",
        ]
        nested_fields = ["import_routing_policies", "export_routing_policies"]


class BGPGroupSerializer(TaggitSerializer, WriteEnabledNestedSerializer):
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
        nested_fields = [
            "import_routing_policies",
            "export_routing_policies",
            "communities",
        ]


class CommunitySerializer(TaggitSerializer, ModelSerializer):
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Community
        fields = ["id", "name", "slug", "value", "type", "comments", "tags"]


class ConfigurationSerializer(TaggitSerializer, ModelSerializer):
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Configuration
        fields = ["id", "name", "template", "comments", "tags"]


class EmailSerializer(TaggitSerializer, ModelSerializer):
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Email
        fields = ["id", "name", "subject", "template", "comments", "tags"]


class RouterSerializer(TaggitSerializer, WriteEnabledNestedSerializer):
    configuration_template = ConfigurationNestedSerializer(required=False)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Router
        fields = [
            "id",
            "name",
            "hostname",
            "platform",
            "encrypt_passwords",
            "configuration_template",
            "last_deployment_id",
            "netbox_device_id",
            "use_netbox",
            "napalm_username",
            "napalm_password",
            "napalm_timeout",
            "napalm_args",
            "comments",
            "tags",
        ]
        nested_fields = ["configuration_template"]


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
            "comments",
            "tags",
        ]


class DirectPeeringSessionSerializer(TaggitSerializer, WriteEnabledNestedSerializer):
    local_autonomous_system = AutonomousSystemNestedSerializer()
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
            "local_autonomous_system",
            "autonomous_system",
            "local_asn",
            "local_ip_address",
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
        nested_fields = [
            "bgp_group",
            "import_routing_policies",
            "export_routing_policies",
            "router",
        ]


class InternetExchangeSerializer(TaggitSerializer, WriteEnabledNestedSerializer):
    local_autonomous_system = AutonomousSystemNestedSerializer()
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
            "local_autonomous_system",
            "name",
            "slug",
            "ipv6_address",
            "ipv4_address",
            "comments",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "router",
            "check_bgp_session_states",
            "bgp_session_states_update",
            "tags",
        ]
        nested_fields = [
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "router",
        ]


class InternetExchangePeeringSessionSerializer(
    TaggitSerializer, WriteEnabledNestedSerializer
):
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
        nested_fields = ["import_routing_policies", "export_routing_policies"]
