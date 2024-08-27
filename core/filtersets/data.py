import django_filters
from django.db.models import Q

from peering_manager.filtersets import (
    ChangeLoggedModelFilterSet,
    PeeringManagerModelFilterSet,
)

from ..enums import DataSourceStatus
from ..models import DataFile, DataSource
from ..utils import get_data_backend_choices

__all__ = ("DataFileFilterSet", "DataSourceFilterSet")


class DataFileFilterSet(ChangeLoggedModelFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    source_id = django_filters.ModelMultipleChoiceFilter(
        queryset=DataSource.objects.all(), label="Data source (ID)"
    )
    source = django_filters.ModelMultipleChoiceFilter(
        field_name="source__name",
        queryset=DataSource.objects.all(),
        to_field_name="name",
        label="Data source (name)",
    )

    class Meta:
        model = DataFile
        fields = ("id", "path", "updated", "size", "hash")

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(path__icontains=value)


class DataSourceFilterSet(PeeringManagerModelFilterSet):
    type = django_filters.MultipleChoiceFilter(
        choices=get_data_backend_choices, null_value=None
    )
    status = django_filters.MultipleChoiceFilter(
        choices=DataSourceStatus, null_value=None
    )

    class Meta:
        model = DataSource
        fields = ("id", "name", "enabled", "description")

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(comments__icontains=value)
        )
