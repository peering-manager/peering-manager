import django_filters
from django.contrib.auth.models import User
from django.db.models import Q

from .enums import ObjectChangeAction
from .models import ObjectChange, Tag


class ObjectChangeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    time = django_filters.DateTimeFromToRangeFilter()
    action = django_filters.MultipleChoiceFilter(
        choices=ObjectChangeAction.choices, null_value=None
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


class CreatedUpdatedFilterSet(django_filters.FilterSet):
    created = django_filters.DateFilter()
    created__gte = django_filters.DateFilter(field_name="created", lookup_expr="gte")
    created__lte = django_filters.DateFilter(field_name="created", lookup_expr="lte")
    updated = django_filters.DateTimeFilter()
    updated__gte = django_filters.DateTimeFilter(
        field_name="updated", lookup_expr="gte"
    )
    updated__lte = django_filters.DateTimeFilter(
        field_name="updated", lookup_expr="lte"
    )


class NameSlugSearchFilterSet(django_filters.FilterSet):
    """
    A base class to add a search method to models which only expose the `name` and
    `slug` fields
    """

    q = django_filters.CharFilter(method="search", label="Search")

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(Q(name__icontains=value) | Q(slug__icontains=value))


class ObjectChangeFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    time = django_filters.DateTimeFromToRangeFilter()
    action = django_filters.MultipleChoiceFilter(
        choices=ObjectChangeAction.choices, null_value=None
    )
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


class TagFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
    class Meta:
        model = Tag
        fields = ["id", "color"]
