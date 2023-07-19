import django_filters
from django.db.models import Q

from peering_manager.filtersets import (
    OrganisationalModelFilterSet,
    PeeringManagerModelFilterSet,
)

from .enums import PasswordAlgorithm
from .models import Configuration, Platform

__all__ = ("ConfigurationFilterSet", "PlatformFilterSet")


class ConfigurationFilterSet(PeeringManagerModelFilterSet):
    class Meta:
        model = Configuration
        fields = ["id", "jinja2_trim", "jinja2_lstrip"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(Q(name__icontains=value) | Q(template__icontains=value))


class PlatformFilterSet(OrganisationalModelFilterSet):
    password_algorithm = django_filters.MultipleChoiceFilter(
        choices=PasswordAlgorithm, null_value=None
    )

    class Meta:
        model = Platform
        fields = ["id", "name", "slug", "napalm_driver", "description"]
