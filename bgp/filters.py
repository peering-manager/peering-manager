from bgp.models import Relationship
from utils.filters import (
    BaseFilterSet,
    CreatedUpdatedFilterSet,
    NameSlugSearchFilterSet,
)


class RelationshipFilterSet(
    BaseFilterSet, CreatedUpdatedFilterSet, NameSlugSearchFilterSet
):
    class Meta:
        model = Relationship
        fields = ["id", "name", "slug"]
