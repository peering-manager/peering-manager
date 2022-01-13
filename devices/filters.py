import django_filters
from django.db.models import Q

from devices.enums import PasswordAlgorithm
from devices.models import Configuration, Platform
from utils.filters import (
    BaseFilterSet,
    CreatedUpdatedFilterSet,
    NameSlugSearchFilterSet,
    TagFilter,
)


class ConfigurationFilterSet(BaseFilterSet, CreatedUpdatedFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    tag = TagFilter()

    class Meta:
        model = Configuration
        fields = ["id", "jinja2_trim", "jinja2_lstrip"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(Q(name__icontains=value) | Q(template__icontains=value))


class PlatformFilterSet(
    BaseFilterSet, CreatedUpdatedFilterSet, NameSlugSearchFilterSet
):
    password_algorithm = django_filters.MultipleChoiceFilter(
        choices=PasswordAlgorithm.choices, null_value=None
    )

    class Meta:
        model = Platform
        fields = ["id", "name", "slug", "napalm_driver", "description"]
