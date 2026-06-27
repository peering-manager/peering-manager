import django_filters
from django.db.models import Q

from peering_manager.filtersets import OrganisationalModelFilterSet

from ..enums import RoutingPolicyType
from ..models import RoutingPolicy

__all__ = ("RoutingPolicyFilterSet",)


class RoutingPolicyFilterSet(OrganisationalModelFilterSet):
    type = django_filters.MultipleChoiceFilter(
        method="type_search", choices=RoutingPolicyType, null_value=None
    )

    class Meta:
        model = RoutingPolicy
        fields = ["id", "weight", "address_family"]

    def type_search(self, queryset, name, value):
        qs_filter = Q(type=RoutingPolicyType.IMPORT_EXPORT)
        for v in value:
            qs_filter |= Q(type=v)
        return queryset.filter(qs_filter)
