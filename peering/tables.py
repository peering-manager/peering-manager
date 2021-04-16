import django_tables2 as tables
from django.utils.safestring import mark_safe

from net.models import Connection
from peering_manager import settings
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
    Configuration,
    DirectPeeringSession,
    Email,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)

BGP_RELATIONSHIP = "{{ record.get_relationship_html }}"
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
    affiliated = BooleanColumn(
        verbose_name="Affiliated",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    tags = TagColumn(url_name="peering:autonomoussystem_list")
    buttons = ButtonsColumn(AutonomousSystem, pk_field="asn")

    class Meta(BaseTable.Meta):
        model = AutonomousSystem
        fields = (
            "pk",
            "asn",
            "name",
            "irr_as_set",
            "ipv6_max_prefixes",
            "ipv4_max_prefixes",
            "import_routing_policies",
            "export_routing_policies",
            "directpeeringsession_count",
            "internetexchangepeeringsession_count",
            "affiliated",
            "tags",
            "buttons",
        )
        default_columns = (
            "pk",
            "asn",
            "name",
            "irr_as_set",
            "directpeeringsession_count",
            "internetexchangepeeringsession_count",
            "buttons",
        )


class BGPGroupTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    check_bgp_session_states = BooleanColumn(
        verbose_name="Poll Session States",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    directpeeringsession_count = tables.Column(
        verbose_name="Direct Sessions",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    tags = TagColumn(url_name="peering:bgpgroup_list")
    buttons = ButtonsColumn(BGPGroup, pk_field="slug")

    class Meta(BaseTable.Meta):
        model = BGPGroup
        fields = (
            "pk",
            "name",
            "slug",
            "check_bgp_session_states",
            "import_routing_policies",
            "export_routing_policies",
            "directpeeringsession_count",
            "tags",
            "buttons",
        )
        default_columns = (
            "pk",
            "name",
            "check_bgp_session_states",
            "directpeeringsession_count",
            "buttons",
        )


class CommunityTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    type = tables.TemplateColumn(template_code=COMMUNITY_TYPE)
    tags = TagColumn(url_name="peering:community_list")
    buttons = ButtonsColumn(Community)

    class Meta(BaseTable.Meta):
        model = Community
        fields = ("pk", "name", "slug", "value", "type", "tags", "buttons")
        default_columns = ("pk", "name", "value", "type", "buttons")


class ConfigurationTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    tags = TagColumn(url_name="peering:configuration_list")
    buttons = ButtonsColumn(Configuration)

    class Meta(BaseTable.Meta):
        model = Configuration
        fields = ("pk", "name", "updated", "tags", "buttons")
        default_columns = ("pk", "name", "updated", "buttons")


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
    enabled = BooleanColumn(
        verbose_name="Status",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    state = BGPSessionStateColumn(accessor="bgp_state")
    router = tables.Column(verbose_name="Router", accessor="router", linkify=True)
    tags = TagColumn(url_name="peering:directpeeringsession_list")
    buttons = ButtonsColumn(DirectPeeringSession, append_template=append_template)

    class Meta(BaseTable.Meta):
        model = DirectPeeringSession
        fields = (
            "pk",
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
            "buttons",
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
            "buttons",
        )


class EmailTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    tags = TagColumn(url_name="peering:configuration_list")
    buttons = ButtonsColumn(Email)

    class Meta(BaseTable.Meta):
        model = Email
        fields = ("pk", "name", "subject", "updated", "tags", "buttons")
        default_columns = ("pk", "name", "updated", "buttons")


class InternetExchangeTable(BaseTable):
    pk = SelectColumn()
    local_autonomous_system = tables.Column(verbose_name="Local AS", linkify=True)
    name = tables.Column(linkify=True)
    check_bgp_session_states = BooleanColumn(
        verbose_name="Check Sessions",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    bgp_session_states_update = tables.Column(verbose_name="Last Sessions Check")
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    internetexchangepeeringsession_count = tables.Column(
        verbose_name="Sessions",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    tags = TagColumn(url_name="peering:internetexchange_list")
    buttons = ButtonsColumn(InternetExchange, pk_field="slug")

    class Meta(BaseTable.Meta):
        model = InternetExchange
        fields = (
            "pk",
            "local_autonomous_system",
            "name",
            "slug",
            "import_routing_policies",
            "export_routing_policies",
            "check_bgp_session_states",
            "bgp_session_states_update",
            "internetexchangepeeringsession_count",
            "tags",
            "buttons",
        )
        default_columns = (
            "pk",
            "name",
            "internetexchangepeeringsession_count",
            "buttons",
        )


class InternetExchangeConnectionTable(BaseTable):
    pk = SelectColumn()
    ipv6_address = tables.Column(linkify=True, verbose_name="IPv6")
    ipv4_address = tables.Column(linkify=True, verbose_name="IPv4")
    router = tables.LinkColumn()
    buttons = ButtonsColumn(Connection)

    class Meta(BaseTable.Meta):
        model = Connection
        fields = (
            "pk",
            "state",
            "vlan",
            "ipv6_address",
            "ipv4_address",
            "router",
            "interface",
            "buttons",
        )
        default_columns = (
            "pk",
            "state",
            "vlan",
            "ipv6_address",
            "ipv4_address",
            "router",
            "buttons",
        )
        empty_text = "None"


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
    is_route_server = BooleanColumn(
        verbose_name="Route Server",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    enabled = BooleanColumn(
        verbose_name="Enabled",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    import_routing_policies = RoutingPolicyColumn(verbose_name="Import Policies")
    export_routing_policies = RoutingPolicyColumn(verbose_name="Export Policies")
    state = BGPSessionStateColumn(accessor="bgp_state")
    tags = TagColumn(url_name="peering:internetexchangepeeringsession_list")
    buttons = ButtonsColumn(
        InternetExchangePeeringSession, append_template=append_template
    )

    class Meta(BaseTable.Meta):
        model = InternetExchangePeeringSession
        fields = (
            "pk",
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
            "buttons",
        )
        default_columns = (
            "pk",
            "autonomous_system",
            "ixp_connection",
            "ip_address",
            "is_route_server",
            "enabled",
            "buttons",
        )


class RouterTable(BaseTable):
    pk = SelectColumn()
    local_autonomous_system = tables.Column(verbose_name="Local AS", linkify=True)
    name = tables.Column(linkify=True)
    platform = tables.Column(linkify=True)
    encrypt_passwords = BooleanColumn(
        verbose_name="Encrypt Password",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
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
    buttons = ButtonsColumn(Router)

    class Meta(BaseTable.Meta):
        model = Router
        fields = (
            "pk",
            "local_autonomous_system",
            "name",
            "hostname",
            "platform",
            "encrypt_passwords",
            "configuration_template",
            "connection_count",
            "directpeeringsession_count",
            "internetexchangepeeringsession_count",
            "device_state",
            "tags",
            "buttons",
        )
        default_columns = (
            "pk",
            "name",
            "hostname",
            "platform",
            "encrypt_passwords",
            "configuration_template",
            "connection_count",
            "device_state",
            "buttons",
        )


class RoutingPolicyTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    type = tables.TemplateColumn(template_code=ROUTING_POLICY_TYPE)
    tags = TagColumn(url_name="peering:routingpolicy_list")
    buttons = ButtonsColumn(RoutingPolicy)

    class Meta(BaseTable.Meta):
        model = RoutingPolicy
        fields = ("pk", "name", "type", "weight", "address_family", "tags", "buttons")
        default_columns = ("pk", "name", "type", "weight", "address_family", "buttons")
