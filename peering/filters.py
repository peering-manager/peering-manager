import ipaddress

from django.db.models import Q

import django_filters

from .enums import BGPRelationship, Platform, RoutingPolicyType
from .models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    Configuration,
    DirectPeeringSession,
    Email,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from utils.filters import TagFilter


class AutonomousSystemFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    tag = TagFilter()

    class Meta:
        model = AutonomousSystem
        fields = [
            "asn",
            "name",
            "irr_as_set",
            "ipv6_max_prefixes",
            "ipv4_max_prefixes",
            "affiliated",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(irr_as_set__icontains=value)
            | Q(comments__icontains=value)
        )
        try:
            qs_filter |= Q(asn=int(value.strip()))
            qs_filter |= Q(ipv6_max_prefixes=int(value.strip()))
            qs_filter |= Q(ipv4_max_prefixes=int(value.strip()))
        except ValueError:
            pass
        return queryset.filter(qs_filter)


class BGPGroupFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    tag = TagFilter()

    class Meta:
        model = BGPGroup
        fields = ["name"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(name__icontains=value)


class CommunityFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    tag = TagFilter()

    class Meta:
        model = Community
        fields = ["name", "value", "slug", "type", "comments"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(slug__icontains=value)
            | Q(value__icontains=value)
            | Q(type__icontains=value)
            | Q(comments__icontains=value)
        )
        return queryset.filter(qs_filter)


class ConfigurationFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    tag = TagFilter()

    class Meta:
        model = Configuration
        fields = ["name", "comments"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(template__icontains=value)
            | Q(comments__icontains=value)
        )
        return queryset.filter(qs_filter)


class DirectPeeringSessionFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    local_autonomous_system = django_filters.ModelMultipleChoiceFilter(
        field_name="local_autonomous_system__id",
        queryset=AutonomousSystem.objects.all(),
        to_field_name="id",
        label="Local AS",
    )
    address_family = django_filters.NumberFilter(method="address_family_search")
    relationship = django_filters.MultipleChoiceFilter(
        choices=BGPRelationship.choices, null_value=None
    )
    router = django_filters.ModelMultipleChoiceFilter(
        field_name="router__id",
        queryset=Router.objects.all(),
        to_field_name="id",
        label="Router",
    )
    tag = TagFilter()

    class Meta:
        model = DirectPeeringSession
        fields = ["multihop_ttl", "enabled"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(relationship__icontains=value) | Q(comments__icontains=value)
        try:
            ip = ipaddress.ip_interface(value.strip())
            qs_filter |= Q(ip_address__host=str(ip)) | Q(local_ip_address__host=str(ip))
        except ValueError:
            pass
        return queryset.filter(qs_filter)

    def address_family_search(self, queryset, name, value):
        if value in [4, 6]:
            return queryset.filter(Q(ip_address__family=value))
        return queryset


class EmailFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    tag = TagFilter()

    class Meta:
        model = Email
        fields = ["name", "comments"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(subject__icontains=value)
            | Q(template__icontains=value)
            | Q(comments__icontains=value)
        )
        return queryset.filter(qs_filter)


class InternetExchangeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    local_autonomous_system = django_filters.ModelMultipleChoiceFilter(
        field_name="local_autonomous_system__id",
        queryset=AutonomousSystem.objects.all(),
        to_field_name="id",
        label="Local AS",
    )
    router = django_filters.ModelMultipleChoiceFilter(
        field_name="router__id",
        queryset=Router.objects.all(),
        to_field_name="id",
        label="Router",
    )
    tag = TagFilter()

    class Meta:
        model = InternetExchange
        fields = [
            "name",
            "slug",
            "local_autonomous_system__asn",
            "local_autonomous_system__id",
            "local_autonomous_system__name",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(comments__icontains=value)
            | Q(autonomous_system__name__icontains=value)
        )
        try:
            qs_filter |= Q(local_autonomous_system__asn=int(value.strip()))
        except ValueError:
            pass
        try:
            ip = ipaddress.ip_interface(value.strip())
            qs_filter |= Q(ipv6_address__host=str(value))
            qs_filter |= Q(ipv4_address__host=str(value))
        except ValueError:
            pass
        return queryset.filter(qs_filter)


class InternetExchangePeeringSessionFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    autonomous_system = django_filters.ModelMultipleChoiceFilter(
        field_name="autonomous_system__id",
        queryset=AutonomousSystem.objects.all(),
        to_field_name="id",
    )
    internet_exchange = django_filters.ModelMultipleChoiceFilter(
        field_name="internet_exchange__id",
        queryset=InternetExchange.objects.all(),
        to_field_name="id",
    )
    address_family = django_filters.NumberFilter(method="address_family_search")
    tag = TagFilter()

    class Meta:
        model = InternetExchangePeeringSession
        fields = [
            "multihop_ttl",
            "enabled",
            "is_route_server",
            "autonomous_system__asn",
            "autonomous_system__id",
            "autonomous_system__name",
            "internet_exchange__name",
            "internet_exchange__id",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(autonomous_system__name__icontains=value)
            | Q(internet_exchange__name__icontains=value)
            | Q(internet_exchange__slug__icontains=value)
            | Q(comments__icontains=value)
        )
        try:
            ip = ipaddress.ip_interface(value.strip())
            qs_filter |= Q(ip_address__host=str(ip))
        except ValueError:
            pass
        try:
            qs_filter |= Q(autonomous_system__asn=int(value.strip()))
        except ValueError:
            pass
        return queryset.filter(qs_filter)

    def address_family_search(self, queryset, name, value):
        if value in [4, 6]:
            return queryset.filter(Q(ip_address__family=value))
        return queryset


class RouterFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    platform = django_filters.MultipleChoiceFilter(
        choices=Platform.choices, null_value=None
    )
    local_autonomous_system = django_filters.ModelMultipleChoiceFilter(
        field_name="local_autonomous_system__id",
        queryset=AutonomousSystem.objects.all(),
        to_field_name="id",
        label="Local AS",
    )
    tag = TagFilter()

    class Meta:
        model = Router
        fields = [
            "name",
            "hostname",
            "encrypt_passwords",
            "configuration_template",
            "last_deployment_id",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(hostname__icontains=value)
            | Q(platform__icontains=value)
            | Q(comments__icontains=value)
        )
        return queryset.filter(qs_filter)


class RoutingPolicyFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    type = django_filters.MultipleChoiceFilter(
        method="type_search", choices=RoutingPolicyType.choices, null_value=None
    )
    tag = TagFilter()

    class Meta:
        model = RoutingPolicy
        fields = ["name", "slug", "weight", "address_family", "comments"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(slug__icontains=value)
            | Q(comments__icontains=value)
        )
        return queryset.filter(qs_filter)

    def type_search(self, queryset, name, value):
        """
        Return routing policies based on
        """
        qs_filter = Q(type=RoutingPolicyType.IMPORT_EXPORT)
        for v in value:
            qs_filter |= Q(type=v)
        return queryset.filter(qs_filter)
