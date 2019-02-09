from rest_framework import serializers

from peering.models import (
    AutonomousSystem,
    Community,
    ConfigurationTemplate,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)


class AutonomousSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutonomousSystem
        fields = [
            "id",
            "asn",
            "name",
            "comment",
            "irr_as_set",
            "irr_as_set_peeringdb_sync",
            "ipv6_max_prefixes",
            "ipv6_max_prefixes_peeringdb_sync",
            "ipv4_max_prefixes",
            "ipv4_max_prefixes_peeringdb_sync",
        ]


class CommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = ["id", "name", "value", "type", "comment"]


class ConfigurationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigurationTemplate
        fields = ["id", "name", "template", "comment"]


class RouterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Router
        fields = ["id", "name", "hostname", "platform", "comment", "netbox_device_id"]


class RoutingPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingPolicy
        fields = ["id", "name", "slug", "type", "comment"]


class DirectPeeringSessionSerializer(serializers.ModelSerializer):
    autonomous_system = AutonomousSystemSerializer()
    import_routing_policies = RoutingPolicySerializer(many=True)
    export_routing_policies = RoutingPolicySerializer(many=True)
    router = RouterSerializer()

    class Meta:
        model = DirectPeeringSession
        fields = [
            "autonomous_system",
            "local_asn",
            "relationship",
            "ip_address",
            "password",
            "enabled",
            "import_routing_policies",
            "export_routing_policies",
            "router",
            "bgp_state",
            "received_prefix_count",
            "advertised_prefix_count",
            "last_established_state",
            "comment",
        ]


class InternetExchangeSerializer(serializers.ModelSerializer):
    configuration_template = ConfigurationTemplateSerializer()
    communities = CommunitySerializer(many=True)
    import_routing_policies = RoutingPolicySerializer(many=True)
    export_routing_policies = RoutingPolicySerializer(many=True)
    router = RouterSerializer()

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
            "communities",
            "import_routing_policies",
            "export_routing_policies",
            "router",
            "check_bgp_session_states",
            "bgp_session_states_update",
        ]


class InternetExchangePeeringSessionSerializer(serializers.ModelSerializer):
    autonomous_system = AutonomousSystemSerializer()
    internet_exchange = InternetExchangeSerializer()
    import_routing_policies = RoutingPolicySerializer(many=True)
    export_routing_policies = RoutingPolicySerializer(many=True)

    class Meta:
        model = InternetExchangePeeringSession
        fields = [
            "autonomous_system",
            "internet_exchange",
            "ip_address",
            "password",
            "enabled",
            "is_route_server",
            "import_routing_policies",
            "export_routing_policies",
            "bgp_state",
            "received_prefix_count",
            "advertised_prefix_count",
            "last_established_state",
            "comment",
        ]
