from peering_manager.filtersets import OrganisationalModelFilterSet

from ..models import BFD

__all__ = ("BFDFilterSet",)


class BFDFilterSet(OrganisationalModelFilterSet):
    class Meta:
        model = BFD
        fields = [
            "id",
            "minimum_transmit_interval",
            "minimum_receive_interval",
            "detection_multiplier",
            "hold_time",
        ]
