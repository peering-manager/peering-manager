import django_filters
from django.db.models import Q

from peering_manager.filtersets import PeeringManagerModelFilterSet

from ..enums import CommunityCategory, CommunityType
from ..models import Community

__all__ = ("CommunityFilterSet",)


class CommunityFilterSet(PeeringManagerModelFilterSet):
    type = django_filters.MultipleChoiceFilter(choices=CommunityType, null_value="")
    category = django_filters.MultipleChoiceFilter(
        choices=CommunityCategory, null_value=""
    )

    class Meta:
        model = Community
        fields = ["id", "value", "type", "category", "private"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(value__icontains=value)
            | Q(slug__icontains=value)
            | Q(description__icontains=value)
        )
