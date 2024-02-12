import django_tables2 as tables

from net.models import Connection
from peering_manager.tables import PeeringManagerTable, columns

from ..models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
    Community,
)
from .columns import BGPSessionStateColumn, RoutingPolicyColumn, CommunityColumn

BGP_RELATIONSHIP = "{{ record.relationship.get_html }}"
COMMUNITY_TYPE = "{{ record.get_type_html }}"
ROUTING_POLICY_TYPE = "{{ record.get_type_html }}"


class AutonomousSystemTable(PeeringManagerTable):
    asn = tables.Column(verbose_name="ASN")
    name = tables.Column(linkify=True)
    irr_as_set = tables.Column(verbose_name="IRR AS-SET", orderable=False)
    ipv6_max_prefixes = tables.Column(verbose_name="IPv6 Max Prefixes")
    ipv4_max_prefixes = tables.Column(verbose_name="IPv4 Max Prefixes")
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    communities = CommunityColumn(verbose_name="Communities")
    directpeeringsession_count = columns.LinkedCountColumn(
        viewname="peering:autonomoussystem_direct_peering_sessions",
        view_kwargs={"pk": True},
        verbose_name="Direct Sessions",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    internetexchangepeeringsession_count = columns.LinkedCountColumn(
        viewname="peering:autonomoussystem_internet_exchange_peering_sessions",
        view_kwargs={"pk": True},
        verbose_name="IX Sessions",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    affiliated = columns.BooleanColumn(verbose_name="Affiliated")
    tags = columns.TagColumn(url_name="peering:autonomoussystem_list")

    class Meta(PeeringManagerTable.Meta):
        model = AutonomousSystem
        fields = (
            "pk",
            "id",
            "asn",
            "name",
            "irr_as_set",
            "ipv6_max_prefixes",
            "ipv4_max_prefixes",
            "general_policy",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "directpeeringsession_count",
            "internetexchangepeeringsession_count",
            "affiliated",
            "tags",
            "actions",
        )
        default_columns = (
            "pk",
            "asn",
            "name",
            "irr_as_set",
            "directpeeringsession_count",
            "internetexchangepeeringsession_count",
            "actions",
        )


class BGPGroupTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    status = columns.ChoiceFieldColumn()
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    communities = CommunityColumn(verbose_name="Communities")
    directpeeringsession_count = tables.Column(
        verbose_name="Direct Sessions",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    tags = columns.TagColumn(url_name="peering:bgpgroup_list")

    class Meta(PeeringManagerTable.Meta):
        model = BGPGroup
        fields = (
            "pk",
            "id",
            "name",
            "slug",
            "status",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "directpeeringsession_count",
            "tags",
            "actions",
        )
        default_columns = (
            "pk",
            "name",
            "status",
            "directpeeringsession_count",
            "actions",
        )


class CommunityTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    type = tables.TemplateColumn(template_code=COMMUNITY_TYPE)
    tags = columns.TagColumn(url_name="peering:community_list")

    class Meta(PeeringManagerTable.Meta):
        model = Community
        fields = ("pk", "name", "slug", "value", "type", "tags", "actions")
        default_columns = ("pk", "name", "value", "type", "actions")


class DirectPeeringSessionTable(PeeringManagerTable):
    append_template = """
    {% load helpers %}
    {% if record.comments %}
    <button type="button" class="btn btn-sm btn-secondary popover-hover" data-toggle="popover" data-html="true" title="Session Comments" data-content="{{ record.comments | markdown:True }}"><i class="fas fa-comment"></i></button>
    {% endif %}
    {% if record.autonomous_system.comments %}
    <button type="button" class="btn btn-sm btn-secondary popover-hover" data-toggle="popover" data-html="true" title="AS Comments" data-content="{{ record.autonomous_system.comments | markdown:True }}"><i class="fas fa-comments"></i></button>
    {% endif %}
    """

    local_autonomous_system = tables.Column(verbose_name="Local AS", linkify=True)
    autonomous_system = tables.Column(verbose_name="AS", linkify=True)
    ip_address = tables.Column(verbose_name="IP Address", linkify=True)
    status = columns.ChoiceFieldColumn()
    bgp_group = tables.Column(
        verbose_name="BGP Group", accessor="bgp_group", linkify=True
    )
    relationship = tables.TemplateColumn(
        verbose_name="Relationship", template_code=BGP_RELATIONSHIP
    )
    passive = columns.BooleanColumn()
    service_reference = tables.Column(verbose_name="Service ID", linkify=True)
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    communities = CommunityColumn(verbose_name="Communities")
    state = BGPSessionStateColumn(accessor="bgp_state")
    router = tables.Column(verbose_name="Router", accessor="router", linkify=True)
    tags = columns.TagColumn(url_name="peering:directpeeringsession_list")
    actions = columns.ActionsColumn(extra_buttons=append_template)

    class Meta(PeeringManagerTable.Meta):
        model = DirectPeeringSession
        fields = (
            "pk",
            "id",
            "service_reference",
            "local_autonomous_system",
            "autonomous_system",
            "bgp_group",
            "relationship",
            "ip_address",
            "status",
            "multihop_ttl",
            "passive",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "state",
            "last_established_state",
            "received_prefix_count",
            "accepted_prefix_count",
            "advertised_prefix_count",
            "router",
            "tags",
            "actions",
        )
        default_columns = (
            "pk",
            "local_autonomous_system",
            "autonomous_system",
            "ip_address",
            "status",
            "bgp_group",
            "relationship",
            "router",
            "actions",
        )


class InternetExchangeTable(PeeringManagerTable):
    local_autonomous_system = tables.Column(verbose_name="Local AS", linkify=True)
    name = tables.Column(linkify=True)
    status = columns.ChoiceFieldColumn()
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    communities = CommunityColumn(verbose_name="Communities")
    connection_count = tables.Column(
        verbose_name="Connections",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    tags = columns.TagColumn(url_name="peering:internetexchange_list")

    class Meta(PeeringManagerTable.Meta):
        model = InternetExchange
        fields = (
            "pk",
            "id",
            "local_autonomous_system",
            "name",
            "slug",
            "status",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "connection_count",
            "tags",
            "actions",
        )
        default_columns = ("pk", "name", "status", "connection_count", "actions")


class InternetExchangePeeringSessionTable(PeeringManagerTable):
    append_template = """
    {% load helpers %}
    {% if record.comments %}
    <button type="button" class="btn btn-sm btn-secondary popover-hover" data-toggle="popover" data-html="true" title="Session Comments" data-content="{{ record.comments | markdown:True }}"><i class="fas fa-comment"></i></button>
    {% endif %}
    {% if record.autonomous_system.comments %}
    <button type="button" class="btn btn-sm btn-secondary popover-hover" data-toggle="popover" data-html="true" title="AS Comments" data-content="{{ record.autonomous_system.comments | markdown:True }}"><i class="fas fa-comments"></i></button>
    {% endif %}
    {% if record.internet_exchange.comments %}
    <button type="button" class="btn btn-sm btn-secondary popover-hover" data-toggle="popover" data-html="true" title="IXP Comments" data-content="{{ record.internet_exchange.comments | markdown:True }}"><i class="fas fa-comment-dots"></i></button>
    {% endif %}
    """

    autonomous_system = tables.Column(
        verbose_name="AS", accessor="autonomous_system", linkify=True
    )
    internet_exchange_point = tables.Column(
        verbose_name="IXP",
        accessor="ixp_connection__internet_exchange_point",
        linkify=True,
    )
    ixp_connection = tables.Column(verbose_name="Connection", linkify=True)
    ip_address = tables.Column(verbose_name="IP Address", linkify=True)
    status = columns.ChoiceFieldColumn()
    service_reference = tables.Column(verbose_name="Service ID", linkify=True)
    passive = columns.BooleanColumn()
    is_route_server = columns.BooleanColumn(verbose_name="Route Server")
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    communities = CommunityColumn(verbose_name="Communities")
    exists_in_peeringdb = columns.BooleanColumn(
        accessor="exists_in_peeringdb", verbose_name="In PeeringDB", orderable=False
    )
    state = BGPSessionStateColumn(accessor="bgp_state")
    tags = columns.TagColumn(url_name="peering:internetexchangepeeringsession_list")
    actions = columns.ActionsColumn(extra_buttons=append_template)

    class Meta(PeeringManagerTable.Meta):
        model = InternetExchangePeeringSession
        fields = (
            "pk",
            "id",
            "service_reference",
            "autonomous_system",
            "ixp_connection",
            "internet_exchange_point",
            "ip_address",
            "status",
            "multihop_ttl",
            "passive",
            "is_route_server",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "exists_in_peeringdb",
            "state",
            "last_established_state",
            "received_prefix_count",
            "accepted_prefix_count",
            "advertised_prefix_count",
            "tags",
            "actions",
        )
        default_columns = (
            "pk",
            "autonomous_system",
            "ixp_connection",
            "ip_address",
            "status",
            "is_route_server",
            "actions",
        )


class RouterConnectionTable(PeeringManagerTable):
    status = columns.ChoiceFieldColumn()
    ipv6_address = tables.Column(linkify=True, verbose_name="IPv6")
    ipv4_address = tables.Column(linkify=True, verbose_name="IPv4")
    internet_exchange_point = tables.Column(linkify=True)

    class Meta(PeeringManagerTable.Meta):
        model = Connection
        fields = (
            "pk",
            "status",
            "vlan",
            "ipv6_address",
            "ipv4_address",
            "internet_exchange_point",
            "interface",
            "actions",
        )
        default_columns = (
            "pk",
            "status",
            "vlan",
            "ipv6_address",
            "ipv4_address",
            "internet_exchange_point",
            "actions",
        )


class RouterTable(PeeringManagerTable):
    local_autonomous_system = tables.Column(verbose_name="Local AS", linkify=True)
    name = tables.Column(linkify=True)
    platform = tables.Column(linkify=True)
    status = columns.ChoiceFieldColumn()
    encrypt_passwords = columns.BooleanColumn(verbose_name="Encrypt Password")
    poll_bgp_sessions_state = columns.BooleanColumn(verbose_name="Poll BGP Sessions")
    configuration_template = tables.Column(linkify=True, verbose_name="Configuration")
    connection_count = tables.Column(
        verbose_name="Connections",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    directpeeringsession_count = tables.Column(
        verbose_name="Direct Sessions",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    internetexchangepeeringsession_count = tables.Column(
        verbose_name="IX Sessions",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    tags = columns.TagColumn(url_name="peering:router_list")

    class Meta(PeeringManagerTable.Meta):
        model = Router
        fields = (
            "pk",
            "id",
            "local_autonomous_system",
            "name",
            "hostname",
            "platform",
            "status",
            "encrypt_passwords",
            "poll_bgp_sessions_state",
            "poll_bgp_sessions_last_updated",
            "configuration_template",
            "connection_count",
            "directpeeringsession_count",
            "internetexchangepeeringsession_count",
            "tags",
            "actions",
        )
        default_columns = (
            "pk",
            "name",
            "hostname",
            "platform",
            "status",
            "encrypt_passwords",
            "poll_bgp_sessions_state",
            "configuration_template",
            "connection_count",
            "actions",
        )


class RoutingPolicyTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    type = tables.TemplateColumn(template_code=ROUTING_POLICY_TYPE)
    tags = columns.TagColumn(url_name="peering:routingpolicy_list")

    class Meta(PeeringManagerTable.Meta):
        model = RoutingPolicy
        fields = (
            "pk",
            "id",
            "name",
            "type",
            "weight",
            "address_family",
            "tags",
            "actions",
        )
        default_columns = ("pk", "name", "type", "weight", "address_family", "actions")
