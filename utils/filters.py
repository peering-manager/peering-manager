import django_filters

from django.contrib.auth.models import User
from django.db.models import Q

from .constants import *
from .models import ObjectChange, Tag


class ObjectChangeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    time = django_filters.DateTimeFromToRangeFilter()
    action = django_filters.MultipleChoiceFilter(
        choices=OBJECT_CHANGE_ACTION_CHOICES, null_value=None
    )
    user = django_filters.ModelMultipleChoiceFilter(
        field_name="user__id",
        queryset=User.objects.all(),
        to_field_name="id",
        label="User",
    )

    class Meta:
        model = ObjectChange
        fields = ["user_name", "request_id", "changed_object_type", "object_repr"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(user_name__icontains=value) | Q(object_repr__icontains=value)
        )


class TagFilter(django_filters.ModelMultipleChoiceFilter):
    """
    Matches on one or more assigned tags.
    If multiple tags are specified (like ?tag=one&tag=two), the queryset is filtered to
    objects matching all tags.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("field_name", "tags__slug")
        kwargs.setdefault("to_field_name", "slug")
        kwargs.setdefault("conjoined", True)
        kwargs.setdefault("queryset", Tag.objects.all())

        super().__init__(*args, **kwargs)


class TagFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = Tag
        fields = ["name", "slug"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(Q(name__icontains=value) | Q(slug__icontains=value))
