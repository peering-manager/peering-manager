import django_tables2 as tables

from net.models import Connection
from utils.tables import BaseTable, ButtonsColumn, SelectColumn


class ConnectionTable(BaseTable):
    pk = SelectColumn()
    ipv6_address = tables.Column(linkify=True, verbose_name="IPv6")
    ipv4_address = tables.Column(linkify=True, verbose_name="IPv4")
    internet_exchange_point = tables.LinkColumn()
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
            "internet_exchange_point",
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
