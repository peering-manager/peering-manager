from rest_framework.serializers import ModelSerializer

from net.api.serializers import ConnectionNestedSerializer
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
from utils.api.serializers import TaggedObjectSerializer

from .nested_serializers import *


class AutonomousSystemSerializer(TaggedObjectSerializer, WriteEnabledNestedSerializer):
    import_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    export_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)

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
            "prefixes",
            "affiliated",
            "tags",
        ]
        nested_fields = ["import_routing_policies", "export_routing_policies"]


class BGPGroupSerializer(TaggedObjectSerializer, WriteEnabledNestedSerializer):
    import_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    export_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    communities = CommunityNestedSerializer(many=True, required=False)

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


class CommunitySerializer(TaggedObjectSerializer, ModelSerializer):
    class Meta:
        model = Community
        fields = ["id", "name", "slug", "value", "type", "comments", "tags"]


class ConfigurationSerializer(TaggedObjectSerializer, ModelSerializer):
    class Meta:
        model = Configuration
        fields = ["id", "name", "template", "comments", "tags"]


class EmailSerializer(TaggedObjectSerializer, ModelSerializer):
    class Meta:
        model = Email
        fields = ["id", "name", "subject", "template", "comments", "tags"]


class RouterSerializer(TaggedObjectSerializer, WriteEnabledNestedSerializer):
    configuration_template = ConfigurationNestedSerializer(required=False)
    local_autonomous_system = AutonomousSystemNestedSerializer()

    class Meta:
        model = Router
        fields = [
            "id",
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
        nested_fields = ["configuration_template"]


class RoutingPolicySerializer(TaggedObjectSerializer, ModelSerializer):
    class Meta:
        model = RoutingPolicy
        fields = [
            "id",
            "name",
            "slug",
            "type",
            "weight",
            "address_family",
            "config_context",
            "comments",
            "tags",
        ]


class DirectPeeringSessionSerializer(
    TaggedObjectSerializer, WriteEnabledNestedSerializer
):
    local_autonomous_system = AutonomousSystemNestedSerializer()
    autonomous_system = AutonomousSystemNestedSerializer()
    bgp_group = BGPGroupNestedSerializer(required=False)
    import_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    export_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    router = RouterNestedSerializer(required=False)

    class Meta:
        model = DirectPeeringSession
        fields = [
            "id",
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
        nested_fields = [
            "bgp_group",
            "import_routing_policies",
            "export_routing_policies",
            "router",
        ]


class InternetExchangeSerializer(TaggedObjectSerializer, WriteEnabledNestedSerializer):
    local_autonomous_system = AutonomousSystemNestedSerializer()
    import_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    export_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    communities = CommunityNestedSerializer(many=True, required=False)

    class Meta:
        model = InternetExchange
        fields = [
            "id",
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
        nested_fields = [
            "import_routing_policies",
            "export_routing_policies",
            "communities",
        ]


class InternetExchangePeeringSessionSerializer(
    TaggedObjectSerializer, WriteEnabledNestedSerializer
):
    autonomous_system = AutonomousSystemNestedSerializer()
    ixp_connection = ConnectionNestedSerializer()
    import_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)
    export_routing_policies = RoutingPolicyNestedSerializer(many=True, required=False)

    class Meta:
        model = InternetExchangePeeringSession
        fields = [
            "id",
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
        nested_fields = ["import_routing_policies", "export_routing_policies"]
