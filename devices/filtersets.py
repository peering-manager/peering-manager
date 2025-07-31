import django_filters
from django.db.models import Q

from peering.models import AutonomousSystem
from peering_manager.filtersets import (
    OrganisationalModelFilterSet,
    PeeringManagerModelFilterSet,
)

from .enums import DeviceStatus, PasswordAlgorithm
from .models import Configuration, Platform, Router

__all__ = ("ConfigurationFilterSet", "PlatformFilterSet", "RouterFilterSet")


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


class RouterFilterSet(PeeringManagerModelFilterSet):
    local_autonomous_system_id = django_filters.ModelMultipleChoiceFilter(
        queryset=AutonomousSystem.objects.all(), label="Local AS (ID)"
    )
    local_autonomous_system_asn = django_filters.ModelMultipleChoiceFilter(
        field_name="local_autonomous_system__asn",
        queryset=AutonomousSystem.objects.all(),
        to_field_name="asn",
        label="Local AS (ASN)",
    )
    local_autonomous_system = django_filters.ModelMultipleChoiceFilter(
        field_name="local_autonomous_system__name",
        queryset=AutonomousSystem.objects.all(),
        to_field_name="name",
        label="Local AS (Name)",
    )
    platform_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Platform.objects.all(), label="Platform (ID)"
    )
    platform = django_filters.ModelMultipleChoiceFilter(
        field_name="platform__name",
        queryset=Platform.objects.all(),
        to_field_name="name",
        label="Platform (Name)",
    )
    status = django_filters.MultipleChoiceFilter(choices=DeviceStatus, null_value=None)
    configuration_template_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Configuration.objects.all(), label="Configuration (ID)"
    )
    configuration_template = django_filters.ModelMultipleChoiceFilter(
        field_name="configuration_template__name",
        queryset=Configuration.objects.all(),
        to_field_name="name",
        label="Configuration (Name)",
    )

    class Meta:
        model = Router
        fields = ["id", "name", "hostname", "encrypt_passwords"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(hostname__icontains=value)
            | Q(platform__name__icontains=value)
        )
