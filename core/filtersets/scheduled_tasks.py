import django_filters

from peering_manager.filtersets import ChangeLoggedModelFilterSet

from ..models import ScheduledTask

__all__ = ("ScheduledTaskFilterSet",)


class ScheduledTaskFilterSet(ChangeLoggedModelFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = ScheduledTask
        fields = ("id", "task", "enabled", "interval")

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(task__icontains=value)
