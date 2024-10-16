import django_filters
from django.contrib.auth.models import User
from django.db.models import Q

from peering_manager.filtersets import BaseFilterSet

from ..enums import ObjectChangeAction
from ..models import ObjectChange

__all__ = ("ObjectChangeFilterSet",)


class ObjectChangeFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    time = django_filters.DateTimeFromToRangeFilter()
    action = django_filters.MultipleChoiceFilter(
        choices=ObjectChangeAction, null_value=None
    )
    user_id = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(), label="User (ID)"
    )
    user = django_filters.ModelMultipleChoiceFilter(
        field_name="user__username",
        queryset=User.objects.all(),
        to_field_name="username",
        label="User name",
    )

    class Meta:
        model = ObjectChange
        fields = [
            "id",
            "user",
            "user_name",
            "request_id",
            "action",
            "changed_object_type_id",
            "changed_object_id",
            "object_repr",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(user_name__icontains=value) | Q(object_repr__icontains=value)
        )
