import django_tables2 as tables

from peering_manager.tables import PeeringManagerTable, columns

from ..models import Connection

__all__ = ("ConnectionTable",)


class ConnectionTable(PeeringManagerTable):
    status = columns.ChoiceFieldColumn()
    mac_address = tables.Column(linkify=True, verbose_name="MAC")
    ipv6_address = tables.Column(linkify=True, verbose_name="IPv6")
    ipv4_address = tables.Column(linkify=True, verbose_name="IPv4")
    internet_exchange_point = tables.Column(linkify=True)
    router = tables.Column(linkify=True)

    class Meta(PeeringManagerTable.Meta):
        model = Connection
        fields = (
            "pk",
            "id",
            "status",
            "vlan",
            "mac_address",
            "ipv6_address",
            "ipv4_address",
            "internet_exchange_point",
            "router",
            "interface",
            "actions",
        )
        default_columns = (
            "pk",
            "status",
            "vlan",
            "ipv6_address",
            "ipv4_address",
            "router",
            "actions",
        )
