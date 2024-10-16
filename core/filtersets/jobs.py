import django_filters
from django.db.models import Q

from peering_manager.filtersets import BaseFilterSet

from ..enums import JobStatus
from ..models import Job

__all__ = ("JobFilterSet",)


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
