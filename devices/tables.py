import django_tables2 as tables

from bgp.tables import CommunityColumn
from net.models import Connection
from peering_manager.tables import PeeringManagerTable, columns

from .models import Configuration, Platform, Router

__all__ = (
    "ConfigurationTable",
    "PlatformTable",
    "RouterConnectionTable",
    "RouterTable",
)


class ConfigurationTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    jinja2_trim = columns.BooleanColumn(verbose_name="Trim")
    jinja2_lstrip = columns.BooleanColumn(verbose_name="Lstrip")
    tags = columns.TagColumn(url_name="devices:configuration_list")

    class Meta(PeeringManagerTable.Meta):
        model = Configuration
        fields = (
            "pk",
            "id",
            "name",
            "jinja2_trim",
            "jinja2_lstrip",
            "updated",
            "tags",
            "actions",
        )
        default_columns = ("pk", "name", "updated", "actions")


class PlatformTable(PeeringManagerTable):
    router_count = tables.Column(
        verbose_name="Routers",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    actions = columns.ActionsColumn(actions=("edit", "delete"))

    class Meta(PeeringManagerTable.Meta):
        model = Platform
        fields = (
            "pk",
            "id",
            "name",
            "router_count",
            "slug",
            "napalm_driver",
            "napalm_args",
            "password_algorithm",
            "description",
            "actions",
        )
        default_columns = (
            "pk",
            "name",
            "router_count",
            "napalm_driver",
            "password_algorithm",
            "description",
            "actions",
        )


class RouterTable(PeeringManagerTable):
    local_autonomous_system = tables.Column(verbose_name="Local AS", linkify=True)
    name = tables.Column(linkify=True)
    platform = tables.Column(linkify=True)
    communities = CommunityColumn()
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
    tags = columns.TagColumn(url_name="devices:router_list")

    class Meta(PeeringManagerTable.Meta):
        model = Router
        fields = (
            "pk",
            "id",
            "local_autonomous_system",
            "name",
            "hostname",
            "platform",
            "communities",
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
