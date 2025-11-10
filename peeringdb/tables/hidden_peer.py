from __future__ import annotations

import django_tables2 as tables

from peering_manager.tables import PeeringManagerTable, SelectColumn, columns

from ..models import HiddenPeer

__all__ = ("HiddenPeerTable",)


class HiddenPeerTable(PeeringManagerTable):
    empty_text = "No hidden peers found."

    pk = SelectColumn()
    asn = tables.Column(
        verbose_name="ASN", accessor="peeringdb_network__asn", linkify=True
    )
    network_name = tables.Column(
        verbose_name="AS Name", accessor="peeringdb_network__name"
    )
    ixp_name = tables.Column(
        verbose_name="IXP Name", accessor="peeringdb_ixlan__ix__name"
    )
    until = tables.DateTimeColumn(verbose_name="Hidden Until")
    is_expired = columns.BooleanColumn(verbose_name="Expired")
    actions = columns.ActionsColumn()

    class Meta(PeeringManagerTable.Meta):
        model = HiddenPeer
        fields = (
            "pk",
            "id",
            "asn",
            "network_name",
            "ixp_name",
            "until",
            "is_expired",
            "actions",
        )
        default_columns = (
            "pk",
            "asn",
            "network_name",
            "ixp_name",
            "until",
            "is_expired",
            "actions",
        )
