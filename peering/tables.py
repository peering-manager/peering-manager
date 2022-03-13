import django_tables2 as tables
from django.utils.safestring import mark_safe

from net.models import Connection
from utils.tables import (
    BaseTable,
    BooleanColumn,
    ButtonsColumn,
    SelectColumn,
    TagColumn,
)

from .models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)

BGP_RELATIONSHIP = "{{ record.relationship.get_html }}"
COMMUNITY_TYPE = "{{ record.get_type_html }}"
ROUTING_POLICY_TYPE = "{{ record.get_type_html }}"


class BGPSessionStateColumn(tables.TemplateColumn):
    def __init__(self, *args, **kwargs):
        default = kwargs.pop("default", "")
        verbose_name = kwargs.pop("verbose_name", "State")
        template_code = kwargs.pop("template_code", "{{ record.get_bgp_state_html }}")
        super().__init__(
            *args,
            default=default,
            verbose_name=verbose_name,
            template_code=template_code,
            **kwargs
        )


class RoutingPolicyColumn(tables.ManyToManyColumn):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            default=mark_safe('<span class="text-muted">&mdash;</span>'),
            separator=" ",
            transform=lambda p: p.get_type_html(display_name=True),
            **kwargs
        )


class AutonomousSystemTable(BaseTable):
    pk = SelectColumn()
    asn = tables.Column(verbose_name="ASN")
    name = tables.Column(linkify=True)
    irr_as_set = tables.Column(verbose_name="IRR AS-SET", orderable=False)
    ipv6_max_prefixes = tables.Column(verbose_name="IPv6 Max Prefixes")
    ipv4_max_prefixes = tables.Column(verbose_name="IPv4 Max Prefixes")
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    directpeeringsession_count = tables.Column(
        verbose_name="Direct Sessions",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    internetexchangepeeringsession_count = tables.Column(
        verbose_name="IX Sessions",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    affiliated = BooleanColumn(verbose_name="Affiliated")
    tags = TagColumn(url_name="peering:autonomoussystem_list")
    actions = ButtonsColumn(AutonomousSystem)

    class Meta(BaseTable.Meta):
        model = AutonomousSystem
        fields = (
            "pk",
            "asn",
            "name",
            "irr_as_set",
            "ipv6_max_prefixes",
            "ipv4_max_prefixes",
            "general_policy",
            "import_routing_policies",
            "export_routing_policies",
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


class BGPGroupTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    directpeeringsession_count = tables.Column(
        verbose_name="Direct Sessions",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    tags = TagColumn(url_name="peering:bgpgroup_list")
    actions = ButtonsColumn(BGPGroup)

    class Meta(BaseTable.Meta):
        model = BGPGroup
        fields = (
            "pk",
            "name",
            "slug",
            "import_routing_policies",
            "export_routing_policies",
            "directpeeringsession_count",
            "tags",
            "actions",
        )
        default_columns = (
            "pk",
            "name",
            "directpeeringsession_count",
            "actions",
        )


class CommunityTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    type = tables.TemplateColumn(template_code=COMMUNITY_TYPE)
    tags = TagColumn(url_name="peering:community_list")
    actions = ButtonsColumn(Community)

    class Meta(BaseTable.Meta):
        model = Community
        fields = ("pk", "name", "slug", "value", "type", "tags", "actions")
        default_columns = ("pk", "name", "value", "type", "actions")


class DirectPeeringSessionTable(BaseTable):
    append_template = """
    {% load helpers %}
    {% if record.comments %}
    <button type="button" class="btn btn-xs btn-info popover-hover" data-toggle="popover" data-html="true" title="Peering Session Comments" data-content="{{ record.comments | markdown:True }}"><i class="fas fa-comment"></i></button>
    {% endif %}
    {% if record.autonomous_system.comments %}
    <button type="button" class="btn btn-xs btn-info popover-hover" data-toggle="popover" data-html="true" title="Autonomous System Comments" data-content="{{ record.autonomous_system.comments | markdown:True }}"><i class="fas fa-comments"></i></button>
    {% endif %}
    """

    pk = SelectColumn()
    local_autonomous_system = tables.Column(verbose_name="Local AS", linkify=True)
    autonomous_system = tables.Column(verbose_name="AS", linkify=True)
    ip_address = tables.Column(verbose_name="IP Address", linkify=True)
    bgp_group = tables.Column(
        verbose_name="BGP Group", accessor="bgp_group", linkify=True
    )
    relationship = tables.TemplateColumn(
        verbose_name="Relationship", template_code=BGP_RELATIONSHIP
    )
    enabled = BooleanColumn(verbose_name="Status")
    service_reference = tables.Column(verbose_name="Service ID", linkify=True)
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    state = BGPSessionStateColumn(accessor="bgp_state")
    router = tables.Column(verbose_name="Router", accessor="router", linkify=True)
    tags = TagColumn(url_name="peering:directpeeringsession_list")
    actions = ButtonsColumn(DirectPeeringSession, append_template=append_template)

    class Meta(BaseTable.Meta):
        model = DirectPeeringSession
        fields = (
            "pk",
            "service_reference",
            "local_autonomous_system",
            "autonomous_system",
            "ip_address",
            "bgp_group",
            "relationship",
            "enabled",
            "import_routing_policies",
            "export_routing_policies",
            "state",
            "last_established_state",
            "received_prefix_count",
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
            "bgp_group",
            "relationship",
            "enabled",
            "router",
            "actions",
        )


class InternetExchangeTable(BaseTable):
    pk = SelectColumn()
    local_autonomous_system = tables.Column(verbose_name="Local AS", linkify=True)
    name = tables.Column(linkify=True)
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    connection_count = tables.Column(
        verbose_name="Connections",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    tags = TagColumn(url_name="peering:internetexchange_list")
    actions = ButtonsColumn(InternetExchange)

    class Meta(BaseTable.Meta):
        model = InternetExchange
        fields = (
            "pk",
            "local_autonomous_system",
            "name",
            "slug",
            "import_routing_policies",
            "export_routing_policies",
            "connection_count",
            "tags",
            "actions",
        )
        default_columns = (
            "pk",
            "name",
            "connection_count",
            "actions",
        )


class InternetExchangePeeringSessionTable(BaseTable):
    append_template = """
    {% load helpers %}
    {% if record.comments %}
    <button type="button" class="btn btn-xs btn-info popover-hover" data-toggle="popover" data-html="true" title="Peering Session Comments" data-content="{{ record.comments | markdown:True }}"><i class="fas fa-comment"></i></button>
    {% endif %}
    {% if record.autonomous_system.comments %}
    <button type="button" class="btn btn-xs btn-info popover-hover" data-toggle="popover" data-html="true" title="Autonomous System Comments" data-content="{{ record.autonomous_system.comments | markdown:True }}"><i class="fas fa-comments"></i></button>
    {% endif %}
    {% if record.internet_exchange.comments %}
    <button type="button" class="btn btn-xs btn-info popover-hover" data-toggle="popover" data-html="true" title="Internet Exchange Comments" data-content="{{ record.internet_exchange.comments | markdown:True }}"><i class="fas fa-comment-dots"></i></button>
    {% endif %}
    """

    pk = SelectColumn()
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
    service_reference = tables.Column(verbose_name="Service ID", linkify=True)
    is_route_server = BooleanColumn(verbose_name="Route Server")
    enabled = BooleanColumn(verbose_name="Enabled")
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    state = BGPSessionStateColumn(accessor="bgp_state")
    tags = TagColumn(url_name="peering:internetexchangepeeringsession_list")
    actions = ButtonsColumn(
        InternetExchangePeeringSession, append_template=append_template
    )

    class Meta(BaseTable.Meta):
        model = InternetExchangePeeringSession
        fields = (
            "pk",
            "service_reference",
            "autonomous_system",
            "ixp_connection",
            "internet_exchange_point",
            "ip_address",
            "is_route_server",
            "enabled",
            "import_routing_policies",
            "export_routing_policies",
            "state",
            "last_established_state",
            "received_prefix_count",
            "advertised_prefix_count",
            "tags",
            "actions",
        )
        default_columns = (
            "pk",
            "autonomous_system",
            "ixp_connection",
            "ip_address",
            "is_route_server",
            "enabled",
            "actions",
        )


class RouterConnectionTable(BaseTable):
    pk = SelectColumn()
    ipv6_address = tables.Column(linkify=True, verbose_name="IPv6")
    ipv4_address = tables.Column(linkify=True, verbose_name="IPv4")
    internet_exchange_point = tables.Column(linkify=True)
    actions = ButtonsColumn(Connection)

    class Meta(BaseTable.Meta):
        model = Connection
        fields = (
            "pk",
            "state",
            "vlan",
            "ipv6_address",
            "ipv4_address",
            "internet_exchange_point",
            "interface",
            "actions",
        )
        default_columns = (
            "pk",
            "state",
            "vlan",
            "ipv6_address",
            "ipv4_address",
            "internet_exchange_point",
            "actions",
        )


class RouterTable(BaseTable):
    pk = SelectColumn()
    local_autonomous_system = tables.Column(verbose_name="Local AS", linkify=True)
    name = tables.Column(linkify=True)
    platform = tables.Column(linkify=True)
    encrypt_passwords = BooleanColumn(verbose_name="Encrypt Password")
    poll_bgp_sessions_state = BooleanColumn(verbose_name="Poll BGP Sessions")
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
    tags = TagColumn(url_name="peering:router_list")
    actions = ButtonsColumn(Router)

    class Meta(BaseTable.Meta):
        model = Router
        fields = (
            "pk",
            "local_autonomous_system",
            "name",
            "hostname",
            "platform",
            "encrypt_passwords",
            "poll_bgp_sessions_state",
            "poll_bgp_sessions_last_updated",
            "configuration_template",
            "connection_count",
            "directpeeringsession_count",
            "internetexchangepeeringsession_count",
            "device_state",
            "tags",
            "actions",
        )
        default_columns = (
            "pk",
            "name",
            "hostname",
            "platform",
            "encrypt_passwords",
            "poll_bgp_sessions_state",
            "configuration_template",
            "connection_count",
            "device_state",
            "actions",
        )


class RoutingPolicyTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    type = tables.TemplateColumn(template_code=ROUTING_POLICY_TYPE)
    tags = TagColumn(url_name="peering:routingpolicy_list")
    actions = ButtonsColumn(RoutingPolicy)

    class Meta(BaseTable.Meta):
        model = RoutingPolicy
        fields = ("pk", "name", "type", "weight", "address_family", "tags", "actions")
        default_columns = ("pk", "name", "type", "weight", "address_family", "actions")
