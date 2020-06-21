import django_tables2 as tables

from .models import Contact, PeerRecord
from utils.tables import BaseTable, SelectColumn


class ContactTable(BaseTable):
    """
    Table for Contact lists
    """

    empty_text = "No contacts found."
    email = tables.Column(verbose_name="E-mail")
    url = tables.Column(verbose_name="URL")

    class Meta(BaseTable.Meta):
        model = Contact
        fields = ("role", "name", "phone", "email", "url")
        default_columns = ("role", "name", "phone", "email")


class PeerRecordTable(BaseTable):
    """
    Table for PeerRecord lists
    """

    empty_text = "No available peers found."
    pk = SelectColumn()
    asn = tables.Column(verbose_name="ASN", accessor="network__asn")
    name = tables.Column(verbose_name="AS Name", accessor="network__name")
    irr_as_set = tables.Column(
        verbose_name="IRR AS-SET", accessor="network__irr_as_set", orderable=False
    )
    ipv6_max_prefixes = tables.Column(
        verbose_name="IPv6", accessor="network__info_prefixes6"
    )
    ipv4_max_prefixes = tables.Column(
        verbose_name="IPv4", accessor="network__info_prefixes4"
    )
    ipv6_address = tables.Column(
        verbose_name="IPv6 Address", accessor="network_ixlan__ipaddr6"
    )
    ipv4_address = tables.Column(
        verbose_name="IPv4 Address", accessor="network_ixlan__ipaddr4"
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
        default_columns = (
            "pk",
            "asn",
            "name",
            "irr_as_set",
            "ipv6_max_prefixes",
            "ipv4_max_prefixes",
            "ipv6_address",
            "ipv4_address",
        )


class ASPeerRecordTable(BaseTable):
    """
    Table for AS PeerRecord lists
    """

    empty_text = "No available peers found."
    pk = SelectColumn()
    ix = tables.Column(verbose_name="Internet Exchange", accessor="network_ixlan__name")
    irr_as_set = tables.Column(
        verbose_name="IRR AS-SET", accessor="network__irr_as_set", orderable=False
    )
    ipv6_max_prefixes = tables.Column(
        verbose_name="IPv6", accessor="network__info_prefixes6"
    )
    ipv4_max_prefixes = tables.Column(
        verbose_name="IPv4", accessor="network__info_prefixes4"
    )
    ipv6_address = tables.Column(
        verbose_name="IPv6 Address", accessor="network_ixlan__ipaddr6"
    )
    ipv4_address = tables.Column(
        verbose_name="IPv4 Address", accessor="network_ixlan__ipaddr4"
    )

    class Meta(BaseTable.Meta):
        model = PeerRecord
        fields = (
            "pk",
            "ix",
            "irr_as_set",
            "ipv6_max_prefixes",
            "ipv4_max_prefixes",
            "ipv6_address",
            "ipv4_address",
        )
        default_columns = (
            "pk",
            "ix",
            "irr_as_set",
            "ipv6_max_prefixes",
            "ipv4_max_prefixes",
            "ipv6_address",
            "ipv4_address",
        )
