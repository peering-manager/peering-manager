import django_tables2 as tables

from .models import (
    AutonomousSystem,
    Community,
    ConfigurationTemplate,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from peeringdb.models import PeerRecord
from utils.tables import ActionsColumn, BaseTable, SelectColumn
from utils.templatetags.helpers import markdown


AUTONOMOUS_SYSTEM_ACTIONS = """
{% if perms.peering.change_autonomoussystem %}
<a href="{% url 'peering:autonomous_system_edit' asn=record.asn %}" class="btn btn-sm btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
AUTONOMOUS_SYSTEM_HAS_POTENTIAL_IX_PEERING_SESSIONS = """
{% if record.has_potential_ix_peering_sessions %}
<span class="text-right" data-toggle="tooltip" data-placement="left" title="Potential Peering Sessions">
  <i class="fas fa-exclamation-circle text-warning"></i>
</span>
{% endif %}
"""
BGPSESSION_STATUS = "{{ record.get_enabled_html }}"
BGP_RELATIONSHIP = "{{ record.get_relationship_html }}"
COMMUNITY_ACTIONS = """
{% if perms.peering.change_community %}
<a href="{% url 'peering:community_edit' pk=record.pk %}" class="btn btn-sm btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
COMMUNITY_TYPE = "{{ record.get_type_html }}"
CONFIGURATION_TEMPLATE_ACTIONS = """
{% if perms.peering.change_configurationtemplate %}
<a href="{% url 'peering:configuration_template_edit' pk=record.pk %}" class="btn btn-sm btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
DIRECT_PEERING_SESSION_ACTIONS = """
{% load helpers %}
{% if record.comment %}
<button type="button" class="btn btn-sm btn-info popover-hover" data-toggle="popover" data-html="true" title="Peering Session Comments" data-content="{{ record.comment | markdown }}"><i class="fas fa-comment"></i></button>
{% endif %}
{% if record.autonomous_system.comment %}
<button type="button" class="btn btn-sm btn-info popover-hover" data-toggle="popover" data-html="true" title="Autonomous System Comments" data-content="{{ record.autonomous_system.comment | markdown }}"><i class="fas fa-comments"></i></button>
{% endif %}
{% if perms.peering.change_directpeeringsession %}
<a href="{% url 'peering:direct_peering_session_edit' pk=record.pk %}" class="btn btn-sm btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
INTERNET_EXCHANGE_ACTIONS = """
{% if perms.peering.change_internetexchange %}
<a href="{% url 'peering:internet_exchange_edit' slug=record.slug %}" class="btn btn-sm btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
INTERNET_EXCHANGE_PEERING_SESSION_ACTIONS = """
{% load helpers %}
{% if record.comment %}
<button type="button" class="btn btn-sm btn-info popover-hover" data-toggle="popover" data-html="true" title="Peering Session Comments" data-content="{{ record.comment | markdown }}"><i class="fas fa-comment"></i></button>
{% endif %}
{% if record.autonomous_system.comment %}
<button type="button" class="btn btn-sm btn-info popover-hover" data-toggle="popover" data-html="true" title="Autonomous System Comments" data-content="{{ record.autonomous_system.comment | markdown }}"><i class="fas fa-comments"></i></button>
{% endif %}
{% if record.internet_exchange.comment %}
<button type="button" class="btn btn-sm btn-info popover-hover" data-toggle="popover" data-html="true" title="Internet Exchange Comments" data-content="{{ record.internet_exchange.comment | markdown }}"><i class="fas fa-comment-dots"></i></button>
{% endif %}
{% if perms.peering.change_internetexchangepeeringsession %}
<a href="{% url 'peering:internet_exchange_peering_session_edit' pk=record.pk %}" class="btn btn-sm btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
INTERNET_EXCHANGE_PEERING_SESSION_IS_ROUTE_SERVER = """
{% if record.is_route_server %}
<i class="fas fa-check-square text-success"></i>
{% else %}
<i class="fas fa-times text-danger"></i>
{% endif %}
"""
ROUTER_ACTIONS = """
{% if perms.peering.change_router %}
<a href="{% url 'peering:router_edit' pk=record.pk %}" class="btn btn-sm btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
ROUTING_POLICY_ACTIONS = """
{% if perms.peering.change_routingpolicy %}
<a href="{% url 'peering:routing_policy_edit' pk=record.pk %}" class="btn btn-sm btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""
ROUTING_POLICY_TYPE = "{{ record.get_type_html }}"


class BGPSessionStateColumn(tables.TemplateColumn):
    template = "{{ record.get_bgp_state_html }}"

    def __init__(self, *args, **kwargs):
        default = kwargs.pop("default", "")
        visible = kwargs.pop("visible", False)
        verbose_name = kwargs.pop("verbose_name", "State")
        template_code = kwargs.pop("template_code", self.template)
        super().__init__(
            *args,
            default=default,
            verbose_name=verbose_name,
            template_code=template_code,
            visible=visible,
            **kwargs
        )


class AutonomousSystemTable(BaseTable):
    """
    Table for AutonomousSystem lists
    """

    pk = SelectColumn()
    asn = tables.Column(verbose_name="ASN")
    name = tables.LinkColumn()
    irr_as_set = tables.Column(verbose_name="IRR AS-SET", orderable=False)
    ipv6_max_prefixes = tables.Column(verbose_name="IPv6 Max Prefixes")
    ipv4_max_prefixes = tables.Column(verbose_name="IPv4 Max Prefixes")
    has_potential_ix_peering_sessions = tables.TemplateColumn(
        verbose_name="",
        orderable=False,
        template_code=AUTONOMOUS_SYSTEM_HAS_POTENTIAL_IX_PEERING_SESSIONS,
    )
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
            "actions",
        )


class CommunityTable(BaseTable):
    """
    Table for Community lists
    """

    pk = SelectColumn()
    name = tables.LinkColumn()
    type = tables.TemplateColumn(template_code=COMMUNITY_TYPE)
    actions = ActionsColumn(template_code=COMMUNITY_ACTIONS)

    class Meta(BaseTable.Meta):
        model = Community
        fields = ("pk", "name", "value", "type", "actions")


class ConfigurationTemplateTable(BaseTable):
    """
    Table for ConfigurationTemplate lists
    """

    pk = SelectColumn()
    name = tables.LinkColumn()
    actions = ActionsColumn(template_code=CONFIGURATION_TEMPLATE_ACTIONS)

    class Meta(BaseTable.Meta):
        model = ConfigurationTemplate
        fields = ("pk", "name", "updated", "actions")


class DirectPeeringSessionTable(BaseTable):
    """
    Table for DirectPeeringSession lists
    """

    pk = SelectColumn()
    local_asn = tables.Column(verbose_name="Local ASN")
    ip_address = tables.LinkColumn(verbose_name="IP Address")
    relationship = tables.TemplateColumn(
        verbose_name="Relationship", template_code=BGP_RELATIONSHIP
    )
    enabled = tables.TemplateColumn(
        verbose_name="Status", template_code=BGPSESSION_STATUS
    )
    session_state = BGPSessionStateColumn(accessor="bgp_state")
    router = tables.RelatedLinkColumn(verbose_name="Router", accessor="router")
    actions = ActionsColumn(template_code=DIRECT_PEERING_SESSION_ACTIONS)

    class Meta(BaseTable.Meta):
        model = DirectPeeringSession
        fields = (
            "pk",
            "local_asn",
            "ip_address",
            "relationship",
            "enabled",
            "session_state",
            "router",
            "actions",
        )


class InternetExchangeTable(BaseTable):
    """
    Table for InternetExchange lists
    """

    pk = SelectColumn()
    name = tables.LinkColumn()
    ipv6_address = tables.Column(verbose_name="IPv6 Address")
    ipv4_address = tables.Column(verbose_name="IPv4 Address")
    configuration_template = tables.RelatedLinkColumn(
        verbose_name="Template", accessor="configuration_template"
    )
    router = tables.RelatedLinkColumn(verbose_name="Router", accessor="router")
    actions = ActionsColumn(template_code=INTERNET_EXCHANGE_ACTIONS)

    class Meta(BaseTable.Meta):
        model = InternetExchange
        fields = (
            "pk",
            "name",
            "ipv6_address",
            "ipv4_address",
            "configuration_template",
            "router",
            "actions",
        )


class InternetExchangePeeringSessionTable(BaseTable):
    """
    Table for InternetExchangePeeringSession lists
    """

    pk = SelectColumn()
    asn = tables.Column(verbose_name="ASN", accessor="autonomous_system.asn")
    autonomous_system = tables.RelatedLinkColumn(
        verbose_name="AS Name",
        accessor="autonomous_system",
        text=lambda record: record.autonomous_system.name,
    )
    internet_exchange = tables.RelatedLinkColumn(
        verbose_name="IX Name", accessor="internet_exchange"
    )
    ip_address = tables.LinkColumn(verbose_name="IP Address")
    is_route_server = tables.TemplateColumn(
        verbose_name="Route Server",
        template_code=INTERNET_EXCHANGE_PEERING_SESSION_IS_ROUTE_SERVER,
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    enabled = tables.TemplateColumn(
        verbose_name="Status", template_code=BGPSESSION_STATUS
    )
    actions = ActionsColumn(template_code=INTERNET_EXCHANGE_PEERING_SESSION_ACTIONS)

    class Meta(BaseTable.Meta):
        model = InternetExchangePeeringSession
        fields = (
            "pk",
            "asn",
            "autonomous_system",
            "internet_exchange",
            "ip_address",
            "is_route_server",
            "enabled",
            "actions",
        )


class InternetExchangePeeringSessionTableForIX(BaseTable):
    """
    Table for InternetExchangePeeringSession lists
    """

    pk = SelectColumn()
    asn = tables.Column(verbose_name="ASN", accessor="autonomous_system.asn")
    autonomous_system = tables.RelatedLinkColumn(
        verbose_name="AS Name",
        accessor="autonomous_system",
        text=lambda record: record.autonomous_system.name,
    )
    ip_address = tables.LinkColumn(verbose_name="IP Address")
    is_route_server = tables.TemplateColumn(
        verbose_name="Route Server",
        template_code=INTERNET_EXCHANGE_PEERING_SESSION_IS_ROUTE_SERVER,
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    enabled = tables.TemplateColumn(
        verbose_name="Status", template_code=BGPSESSION_STATUS
    )
    session_state = BGPSessionStateColumn(accessor="bgp_state")
    actions = ActionsColumn(template_code=INTERNET_EXCHANGE_PEERING_SESSION_ACTIONS)

    class Meta(BaseTable.Meta):
        model = InternetExchangePeeringSession
        fields = (
            "pk",
            "asn",
            "autonomous_system",
            "ip_address",
            "is_route_server",
            "enabled",
            "session_state",
            "actions",
        )


class InternetExchangePeeringSessionTableForAS(BaseTable):
    """
    Table for InternetExchangePeeringSession lists
    """

    pk = SelectColumn()
    internet_exchange = tables.RelatedLinkColumn(
        verbose_name="Internet Exchange", accessor="internet_exchange"
    )
    ip_address = tables.LinkColumn(verbose_name="IP Address")
    is_route_server = tables.TemplateColumn(
        verbose_name="Route Server",
        template_code=INTERNET_EXCHANGE_PEERING_SESSION_IS_ROUTE_SERVER,
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    enabled = tables.TemplateColumn(
        verbose_name="Status", template_code=BGPSESSION_STATUS
    )
    session_state = BGPSessionStateColumn(accessor="bgp_state")
    actions = ActionsColumn(template_code=INTERNET_EXCHANGE_PEERING_SESSION_ACTIONS)

    class Meta(BaseTable.Meta):
        model = InternetExchangePeeringSession
        fields = (
            "pk",
            "internet_exchange",
            "ip_address",
            "is_route_server",
            "enabled",
            "session_state",
            "actions",
        )


class PeerRecordTable(BaseTable):
    """
    Table for PeerRecord lists
    """

    empty_text = "No available peers found."
    pk = SelectColumn()
    asn = tables.Column(verbose_name="ASN", accessor="network.asn")
    name = tables.Column(verbose_name="AS Name", accessor="network.name")
    irr_as_set = tables.Column(
        verbose_name="IRR AS-SET", accessor="network.irr_as_set", orderable=False
    )
    ipv6_max_prefixes = tables.Column(
        verbose_name="IPv6", accessor="network.info_prefixes6"
    )
    ipv4_max_prefixes = tables.Column(
        verbose_name="IPv4", accessor="network.info_prefixes4"
    )
    ipv6_address = tables.Column(
        verbose_name="IPv6 Address", accessor="network_ixlan.ipaddr6"
    )
    ipv4_address = tables.Column(
        verbose_name="IPv4 Address", accessor="network_ixlan.ipaddr4"
    )

    class Meta(BaseTable.Meta):
        model = PeerRecord
        fields = (
            "pk",
            "asn",
            "name",
            "irr_as_set",
            "ipv6_max_prefixes",
            "ipv4_max_prefixes",
            "ipv6_address",
            "ipv4_address",
        )


class RouterTable(BaseTable):
    """
    Table for Router lists
    """

    pk = SelectColumn()
    name = tables.LinkColumn()
    actions = ActionsColumn(template_code=ROUTER_ACTIONS)

    class Meta(BaseTable.Meta):
        model = Router
        fields = ("pk", "name", "hostname", "platform", "actions")


class RoutingPolicyTable(BaseTable):
    """
    Table for RoutingPolicy lists
    """

    pk = SelectColumn()
    name = tables.LinkColumn()
    type = tables.TemplateColumn(template_code=ROUTING_POLICY_TYPE)
    actions = ActionsColumn(template_code=ROUTING_POLICY_ACTIONS)

    class Meta(BaseTable.Meta):
        model = RoutingPolicy
        fields = ("pk", "name", "type", "actions")
