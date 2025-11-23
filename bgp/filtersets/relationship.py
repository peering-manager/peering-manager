from peering_manager.filtersets import OrganisationalModelFilterSet

from ..models import Relationship

__all__ = ("RelationshipFilterSet",)


class RelationshipFilterSet(OrganisationalModelFilterSet):
    class Meta:
        model = Relationship
        fields = ["id", "name", "slug"]
