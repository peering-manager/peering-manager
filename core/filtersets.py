import django_filters
from django.db.models import Q

from peering_manager.filtersets import (
    BaseFilterSet,
    ChangeLoggedModelFilterSet,
    PeeringManagerModelFilterSet,
)

from .enums import DataSourceStatus, JobStatus
from .models import DataFile, DataSource, Job
from .utils import get_data_backend_choices


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


class JobFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    created = django_filters.DateTimeFilter()
    created__before = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="lte"
    )
    created__after = django_filters.DateTimeFilter(
        field_name="created", lookup_expr="gte"
    )
    started = django_filters.DateTimeFilter()
    started__before = django_filters.DateTimeFilter(
        field_name="started", lookup_expr="lte"
    )
    started__after = django_filters.DateTimeFilter(
        field_name="started", lookup_expr="gte"
    )
    completed = django_filters.DateTimeFilter()
    completed__before = django_filters.DateTimeFilter(
        field_name="completed", lookup_expr="lte"
    )
    completed__after = django_filters.DateTimeFilter(
        field_name="completed", lookup_expr="gte"
    )
    status = django_filters.MultipleChoiceFilter(choices=JobStatus, null_value=None)

    class Meta:
        model = Job
        fields = ("id", "object_type", "object_id", "name", "status", "user")

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(user__username__icontains=value) | Q(name__icontains=value)
        )
