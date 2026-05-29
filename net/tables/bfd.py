from peering_manager.tables import PeeringManagerTable, columns

from ..models import BFD

__all__ = ("BFDTable",)


class BFDTable(PeeringManagerTable):
    tags = columns.TagColumn(url_name="net:bfd_list")

    class Meta(PeeringManagerTable.Meta):
        model = BFD
        fields = (
            "pk",
            "id",
            "name",
            "slug",
            "description",
            "minimum_transmit_interval",
            "minimum_receive_interval",
            "detection_multiplier",
            "hold_time",
            "tags",
            "actions",
        )
        default_columns = ("pk", "id", "name", "actions")
