import django_tables2 as tables

from .models import PeerRecord
from utils.tables import BaseTable, SelectColumn


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
