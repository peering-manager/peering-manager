import django_filters

from .constants import *
from .models import ObjectChange


class ObjectChangeFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    time = django_filters.DateTimeFromToRangeFilter()
    action = django_filters.MultipleChoiceFilter(
        choices=OBJECT_CHANGE_ACTION_CHOICES, null_value=None
    )

    class Meta:
        model = ObjectChange
        fields = [
            "user",
            "user_name",
            "request_id",
            "changed_object_type",
            "object_repr",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(user_name__icontains=value) | Q(object_repr__icontains=value)
        )
