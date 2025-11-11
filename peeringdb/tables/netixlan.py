from __future__ import annotations

from typing import TYPE_CHECKING

import django_tables2 as tables

from peering_manager.tables import ActionsColumn, BaseTable, BooleanColumn, SelectColumn
from utils.templatetags.helpers import render_bandwidth_speed

from ..models import NetworkIXLan

if TYPE_CHECKING:
    from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface

__all__ = ("NetworkIXLanTable",)


class NetworkIXLanTable(BaseTable):
    """
    Table for Network IX LAN lists
    """

    empty_text = "No peers found."
    append_template = """
    {% if instance %}
    {% load helpers %}
    <a href="{% url 'peeringdb:hiddenpeer_add' %}?peeringdb_network={{ record.net.pk }}&peeringdb_ixlan={{ record.ixlan.pk }}&return_url={% url 'peering:internetexchange_peers' pk=instance.pk %}" class="btn btn-secondary btn-sm">
      <i class="fa-solid fa-square-minus"></i>Hide
    </a>
    {% endif %}
    """
    pk = SelectColumn()
    name = tables.Column(verbose_name="AS Name", accessor="net__name")
    internet_exchange = tables.Column(
        verbose_name="IX Name", accessor="ixlan__ix__name"
    )
    ipaddr6 = tables.Column("IPv6", accessor="ipaddr6")
    ipaddr4 = tables.Column("IPv4", accessor="ipaddr4")
    irr_as_set = tables.Column(verbose_name="IRR AS-SET", accessor="net__irr_as_set")
    ipv6_max_prefix = tables.Column(
        verbose_name="IPv6 Max Prefix", accessor="net__info_prefixes6"
    )
    ipv4_max_prefix = tables.Column(
        verbose_name="IPv4 Max Prefix", accessor="net__info_prefixes4"
    )
    is_rs_peer = BooleanColumn(
        verbose_name="On RS",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    bfd_support = BooleanColumn(
        verbose_name="BFD Support",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    operational = BooleanColumn(
        verbose_name="Operational",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    info_traffic = tables.Column(verbose_name="Traffic", accessor="net__info_traffic")
    info_scope = tables.Column(verbose_name="Scope", accessor="net__info_scope")
    info_type = tables.Column(verbose_name="Type", accessor="net__info_type")
    policy = tables.Column(verbose_name="Policy", accessor="net__policy_general")
    policy_locations = tables.Column(
        verbose_name="Multiple Locations",
        accessor="net__policy_locations",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    policy_ratio = BooleanColumn(
        verbose_name="Ratio Requirement", accessor="net__policy_ratio"
    )
    policy_contracts = tables.Column(
        verbose_name="Contract Requirement", accessor="net__policy_contracts"
    )
    actions = ActionsColumn(actions=(), extra_buttons=append_template)

    class Meta(BaseTable.Meta):
        model = NetworkIXLan
        fields = (
            "pk",
            "asn",
            "name",
            "internet_exchange",
            "ipaddr6",
            "ipaddr4",
            "irr_as_set",
            "ipv6_max_prefix",
            "ipv4_max_prefix",
            "is_rs_peer",
            "bfd_support",
            "speed",
            "operational",
            "info_traffic",
            "info_scope",
            "info_type",
            "policy",
            "policy_locations",
            "policy_ratio",
            "policy_contracts",
            "actions",
        )
        default_columns = (
            "pk",
            "asn",
            "name",
            "internet_exchange",
            "ipaddr6",
            "ipaddr4",
            "is_rs_peer",
            "speed",
            "actions",
        )

    def render_ipaddr6(self, value: IPv6Interface) -> IPv6Address | None:
        return value.ip if value else None

    def render_ipaddr4(self, value: IPv4Interface) -> IPv4Address | None:
        return value.ip if value else None

    def render_speed(self, value) -> str:
        return render_bandwidth_speed(value)
