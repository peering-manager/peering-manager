import django_filters
from django.contrib.auth.models import User
from django.db.models import Q

from utils.filters import BaseFilterSet, ContentTypeFilter

from .enums import JobResultStatus
from .models import JobResult


class JobResultFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    obj_type = ContentTypeFilter()
    created = django_filters.DateTimeFilter()
    completed = django_filters.DateTimeFilter()
    user_id = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        label="User (ID)",
    )
    user = django_filters.ModelMultipleChoiceFilter(
        field_name="user__username",
        queryset=User.objects.all(),
        to_field_name="username",
        label="User name",
    )
    status = django_filters.MultipleChoiceFilter(
        choices=JobResultStatus.choices, null_value=None
    )

    class Meta:
        model = JobResult
        fields = ["id", "created", "completed", "status", "user", "obj_type", "name"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(user__username__icontains=value)
        )
