from peering_manager.tables import PeeringManagerTable

from ..models import BFD

__all__ = ("BFDTable",)


class BFDTable(PeeringManagerTable):
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
            "actions",
        )
        default_columns = ("pk", "id", "name", "actions")
