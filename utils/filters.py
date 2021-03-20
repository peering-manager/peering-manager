from copy import deepcopy

import django_filters
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django_filters.constants import EMPTY_VALUES
from django_filters.utils import get_model_field, resolve_field

from .enums import ObjectChangeAction
from .fields import multivalue_field_factory
from .models import ObjectChange, Tag


class ContentTypeFilter(django_filters.CharFilter):
    """
    Allows giving a ContentType by <app_label>.<model> like "peering.router".
    """

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs

        try:
            app_label, model = value.lower().split(".")
        except ValueError:
            return qs.none()
        return qs.filter(
            **{
                f"{self.field_name}__app_label": app_label,
                f"{self.field_name}__model": model,
            }
        )


class ContentTypeMultipleChoiceFilter(django_filters.MultipleChoiceFilter):
    """
    Allows multiple-choice ContentType filtering by <app_label>.<model>.

    By default, it joins multiple options with "AND".
    Use `conjoined=False` to override this behavior to join with "OR" instead.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("conjoined", True)
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        for v in value:
            qs = ContentTypeFilter.filter(self, qs, v)

        return qs


class MultiValueCharFilter(django_filters.MultipleChoiceFilter):
    field_class = multivalue_field_factory(forms.CharField)


class MultiValueDateFilter(django_filters.MultipleChoiceFilter):
    field_class = multivalue_field_factory(forms.DateField)


class MultiValueDateTimeFilter(django_filters.MultipleChoiceFilter):
    field_class = multivalue_field_factory(forms.DateTimeField)


class MultiValueNumberFilter(django_filters.MultipleChoiceFilter):
    field_class = multivalue_field_factory(forms.IntegerField)


class MultiValueTimeFilter(django_filters.MultipleChoiceFilter):
    field_class = multivalue_field_factory(forms.TimeField)


class NullableCharFieldFilter(django_filters.CharFilter):
    """
    Allows matching on null field values by passing a special string meaning NULL.
    """

    def filter(self, qs, value):
        if value != settings.FILTERS_NULL_CHOICE_VALUE:
            return super().filter(qs, value)
        qs = self.get_method(qs)(**{f"{self.field_name}__isnull": True})
        return qs.distinct() if self.distinct else qs


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


class BaseFilterSet(django_filters.FilterSet):
    """
    Base filterset providing common behaviours to all filtersets.
    """

    FILTER_DEFAULTS = deepcopy(django_filters.filterset.FILTER_FOR_DBFIELD_DEFAULTS)
    FILTER_DEFAULTS.update(
        {
            models.AutoField: {"filter_class": MultiValueNumberFilter},
            models.CharField: {"filter_class": MultiValueCharFilter},
            models.DateField: {"filter_class": MultiValueDateFilter},
            models.DateTimeField: {"filter_class": MultiValueDateTimeFilter},
            models.DecimalField: {"filter_class": MultiValueNumberFilter},
            models.EmailField: {"filter_class": MultiValueCharFilter},
            models.FloatField: {"filter_class": MultiValueNumberFilter},
            models.IntegerField: {"filter_class": MultiValueNumberFilter},
            models.PositiveIntegerField: {"filter_class": MultiValueNumberFilter},
            models.PositiveSmallIntegerField: {"filter_class": MultiValueNumberFilter},
            models.SlugField: {"filter_class": MultiValueCharFilter},
            models.SmallIntegerField: {"filter_class": MultiValueNumberFilter},
            models.TimeField: {"filter_class": MultiValueTimeFilter},
            models.URLField: {"filter_class": MultiValueCharFilter},
        }
    )


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
