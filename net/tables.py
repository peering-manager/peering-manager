import django_tables2 as tables

from net.models import Connection
from utils.tables import BaseTable, ButtonsColumn, ChoiceFieldColumn, SelectColumn


class ConnectionTable(BaseTable):
    pk = SelectColumn()
    status = ChoiceFieldColumn()
    ipv6_address = tables.Column(linkify=True, verbose_name="IPv6")
    ipv4_address = tables.Column(linkify=True, verbose_name="IPv4")
    internet_exchange_point = tables.Column(linkify=True)
    router = tables.Column(linkify=True)
    actions = ButtonsColumn(Connection)

    class Meta(BaseTable.Meta):
        model = Connection
        fields = (
            "pk",
            "status",
            "vlan",
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
