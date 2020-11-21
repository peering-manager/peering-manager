import django_tables2 as tables

from django.utils.safestring import mark_safe

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
from peering_manager import settings
from utils.tables import (
    ActionsColumn,
    BaseTable,
    BooleanColumn,
    SelectColumn,
    TagColumn,
)


AUTONOMOUS_SYSTEM_ACTIONS = """
{% if perms.peering.change_autonomoussystem %}
<a href="{% url 'peering:autonomoussystem_edit' asn=record.asn %}" class="btn btn-xs btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
AUTONOMOUS_SYSTEM_HAS_POTENTIAL_IX_PEERING_SESSIONS = """
{% if record.has_potential_ix_peering_sessions %}
<span class="text-right" data-toggle="tooltip" data-placement="left" title="Potential Peering Sessions">
  <i class="fas fa-exclamation-circle text-warning"></i>
</span>
{% endif %}
"""
BGP_GROUP_ACTIONS = """
{% if perms.peering.change_bgpgroup %}
<a href="{% url 'peering:bgpgroup_edit' slug=record.slug %}" class="btn btn-xs btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
BGP_RELATIONSHIP = "{{ record.get_relationship_html }}"
COMMUNITY_ACTIONS = """
{% if perms.peering.change_community %}
<a href="{% url 'peering:community_edit' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
COMMUNITY_TYPE = "{{ record.get_type_html }}"
CONFIGURATION_ACTIONS = """
{% if perms.peering.change_configuration %}
<a href="{% url 'peering:configuration_edit' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
DIRECT_PEERING_SESSION_ACTIONS = """
{% load helpers %}
{% if record.comments %}
<button type="button" class="btn btn-xs btn-info popover-hover" data-toggle="popover" data-html="true" title="Peering Session Comments" data-content="{{ record.comments | markdown }}"><i class="fas fa-comment"></i></button>
{% endif %}
{% if record.autonomous_system.comments %}
<button type="button" class="btn btn-xs btn-info popover-hover" data-toggle="popover" data-html="true" title="Autonomous System Comments" data-content="{{ record.autonomous_system.comments | markdown }}"><i class="fas fa-comments"></i></button>
{% endif %}
{% if perms.peering.change_directpeeringsession %}
<a href="{% url 'peering:directpeeringsession_edit' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
EMAIL_ACTIONS = """
{% if perms.peering.change_email %}
<a href="{% url 'peering:email_edit' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
INTERNET_EXCHANGE_ACTIONS = """
{% if perms.peering.change_internetexchange %}
<a href="{% url 'peering:internetexchange_edit' slug=record.slug %}" class="btn btn-xs btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
INTERNET_EXCHANGE_PEERING_SESSION_ACTIONS = """
{% load helpers %}
{% if record.comments %}
<button type="button" class="btn btn-xs btn-info popover-hover" data-toggle="popover" data-html="true" title="Peering Session Comments" data-content="{{ record.comments | markdown }}"><i class="fas fa-comment"></i></button>
{% endif %}
{% if record.autonomous_system.comments %}
<button type="button" class="btn btn-xs btn-info popover-hover" data-toggle="popover" data-html="true" title="Autonomous System Comments" data-content="{{ record.autonomous_system.comments | markdown }}"><i class="fas fa-comments"></i></button>
{% endif %}
{% if record.internet_exchange.comments %}
<button type="button" class="btn btn-xs btn-info popover-hover" data-toggle="popover" data-html="true" title="Internet Exchange Comments" data-content="{{ record.internet_exchange.comments | markdown }}"><i class="fas fa-comment-dots"></i></button>
{% endif %}
{% if perms.peering.change_internetexchangepeeringsession %}
<a href="{% url 'peering:internetexchangepeeringsession_edit' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
ROUTER_ACTIONS = """
{% if perms.peering.change_router %}
<a href="{% url 'peering:router_edit' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
ROUTING_POLICY_ACTIONS = """
{% if perms.peering.change_routingpolicy %}
<a href="{% url 'peering:routingpolicy_edit' pk=record.pk %}" class="btn btn-xs btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
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
    """
    Table for AutonomousSystem lists
    """

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
    has_potential_ix_peering_sessions = tables.TemplateColumn(
        verbose_name="",
        orderable=False,
        template_code=AUTONOMOUS_SYSTEM_HAS_POTENTIAL_IX_PEERING_SESSIONS,
    )
    affiliated = BooleanColumn(
        verbose_name="Affiliated",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    tags = TagColumn(url_name="peering:autonomoussystem_list")
    actions = ActionsColumn(template_code=AUTONOMOUS_SYSTEM_ACTIONS)

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
            "has_potential_ix_peering_sessions",
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
            "has_potential_ix_peering_sessions",
            "actions",
        )


class BGPGroupTable(BaseTable):
    """
    Table for BGPGroup lists
    """

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
    actions = ActionsColumn(template_code=BGP_GROUP_ACTIONS)

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
            "actions",
        )
        default_columns = (
            "pk",
            "name",
            "check_bgp_session_states",
            "directpeeringsession_count",
            "actions",
        )


class CommunityTable(BaseTable):
    """
    Table for Community lists
    """

    pk = SelectColumn()
    name = tables.Column(linkify=True)
    type = tables.TemplateColumn(template_code=COMMUNITY_TYPE)
    tags = TagColumn(url_name="peering:community_list")
    actions = ActionsColumn(template_code=COMMUNITY_ACTIONS)

    class Meta(BaseTable.Meta):
        model = Community
        fields = ("pk", "name", "slug", "value", "type", "tags", "actions")
        default_columns = ("pk", "name", "value", "type", "actions")


class ConfigurationTable(BaseTable):
    """
    Table for Configuration lists
    """

    pk = SelectColumn()
    name = tables.Column(linkify=True)
    tags = TagColumn(url_name="peering:configuration_list")
    actions = ActionsColumn(template_code=CONFIGURATION_ACTIONS)

    class Meta(BaseTable.Meta):
        model = Configuration
        fields = ("pk", "name", "updated", "tags", "actions")
        default_columns = ("pk", "name", "updated", "actions")


class DirectPeeringSessionTable(BaseTable):
    """
    Table for DirectPeeringSession lists
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
    actions = ActionsColumn(template_code=DIRECT_PEERING_SESSION_ACTIONS)

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


class EmailTable(BaseTable):
    """
    Table for Email lists
    """

    pk = SelectColumn()
    name = tables.Column(linkify=True)
    tags = TagColumn(url_name="peering:configuration_list")
    actions = ActionsColumn(template_code=EMAIL_ACTIONS)

    class Meta(BaseTable.Meta):
        model = Email
        fields = ("pk", "name", "subject", "updated", "tags", "actions")
        default_columns = ("pk", "name", "updated", "actions")


class InternetExchangeTable(BaseTable):
    """
    Table for InternetExchange lists
    """

    pk = SelectColumn()
    local_autonomous_system = tables.Column(verbose_name="Local AS", linkify=True)
    name = tables.Column(linkify=True)
    ipv6_address = tables.Column(verbose_name="IPv6 Address")
    ipv4_address = tables.Column(verbose_name="IPv4 Address")
    router = tables.Column(verbose_name="Router", accessor="router", linkify=True)
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
    actions = ActionsColumn(template_code=INTERNET_EXCHANGE_ACTIONS)

    class Meta(BaseTable.Meta):
        model = InternetExchange
        fields = (
            "pk",
            "local_autonomous_system",
            "name",
            "slug",
            "ipv6_address",
            "ipv4_address",
            "import_routing_policies",
            "export_routing_policies",
            "router",
            "check_bgp_session_states",
            "bgp_session_states_update",
            "internetexchangepeeringsession_count",
            "tags",
            "actions",
        )
        default_columns = (
            "pk",
            "name",
            "ipv6_address",
            "ipv4_address",
            "router",
            "internetexchangepeeringsession_count",
            "actions",
        )


class InternetExchangePeeringSessionTable(BaseTable):
    """
    Table for InternetExchangePeeringSession lists
    """

    pk = SelectColumn()
    autonomous_system = tables.Column(
        verbose_name="AS", accessor="autonomous_system", linkify=True
    )
    internet_exchange = tables.Column(
        verbose_name="IX", accessor="internet_exchange", linkify=True
    )
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
    actions = ActionsColumn(template_code=INTERNET_EXCHANGE_PEERING_SESSION_ACTIONS)

    class Meta(BaseTable.Meta):
        model = InternetExchangePeeringSession
        fields = (
            "pk",
            "autonomous_system",
            "internet_exchange",
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
            "internet_exchange",
            "ip_address",
            "is_route_server",
            "enabled",
            "enabled",
            "actions",
        )


class RouterTable(BaseTable):
    """
    Table for Router lists
    """

    pk = SelectColumn()
    local_autonomous_system = tables.Column(verbose_name="Local AS", linkify=True)
    name = tables.Column(linkify=True)
    encrypt_passwords = BooleanColumn(
        verbose_name="Encrypt Password",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    configuration_template = tables.Column(linkify=True, verbose_name="Configuration")
    directpeeringsession_count = tables.Column(
        verbose_name="Direct Sessions",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    internetexchangepeeringsession_count = tables.Column(
        verbose_name="IX Sessions",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    tags = TagColumn(url_name="peering:router_list")
    actions = ActionsColumn(template_code=ROUTER_ACTIONS)

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
            "last_deployment_id",
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
            "encrypt_passwords",
            "configuration_template",
            "directpeeringsession_count",
            "internetexchangepeeringsession_count",
            "actions",
        )


class RoutingPolicyTable(BaseTable):
    """
    Table for RoutingPolicy lists
    """

    pk = SelectColumn()
    name = tables.Column(linkify=True)
    type = tables.TemplateColumn(template_code=ROUTING_POLICY_TYPE)
    tags = TagColumn(url_name="peering:routingpolicy_list")
    actions = ActionsColumn(template_code=ROUTING_POLICY_ACTIONS)

    class Meta(BaseTable.Meta):
        model = RoutingPolicy
        fields = ("pk", "name", "type", "weight", "address_family", "tags", "actions")
        default_columns = ("pk", "name", "type", "weight", "address_family", "actions")
