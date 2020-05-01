import ipaddress

from django.db.models import Q

import django_filters

from .constants import (
    BGP_RELATIONSHIP_CHOICES,
    PLATFORM_CHOICES,
    ROUTING_POLICY_TYPE_CHOICES,
    ROUTING_POLICY_TYPE_IMPORT_EXPORT,
    TEMPLATE_TYPE_CHOICES,
)
from .models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
    Template,
)
from utils.filters import TagFilter


class AutonomousSystemFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    tag = TagFilter()

    class Meta:
        model = AutonomousSystem
        fields = ["asn", "name", "irr_as_set", "ipv6_max_prefixes", "ipv4_max_prefixes"]

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
        fields = ["name", "value", "type", "comments"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(value__icontains=value)
            | Q(type__icontains=value)
            | Q(comments__icontains=value)
        )
        return queryset.filter(qs_filter)


class DirectPeeringSessionFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    address_family = django_filters.NumberFilter(method="address_family_search")
    relationship = django_filters.MultipleChoiceFilter(
        choices=BGP_RELATIONSHIP_CHOICES, null_value=None
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
        fields = ["local_asn", "multihop_ttl", "enabled"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(relationship__icontains=value) | Q(comments__icontains=value)
        try:
            ip = ipaddress.ip_interface(value.strip())
            qs_filter |= Q(ip_address__host=str(ip)) | Q(local_ip_address__host=str(ip))
        except ValueError:
            pass
        try:
            qs_filter |= Q(local_asn=int(value.strip()))
        except ValueError:
            pass
        return queryset.filter(qs_filter)

    def address_family_search(self, queryset, name, value):
        if value in [4, 6]:
            return queryset.filter(Q(ip_address__family=value))
        return queryset


class InternetExchangeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    router = django_filters.ModelMultipleChoiceFilter(
        field_name="router__id",
        queryset=Router.objects.all(),
        to_field_name="id",
        label="Router",
    )
    tag = TagFilter()

    class Meta:
        model = InternetExchange
        fields = ["name", "slug"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value) | Q(comments__icontains=value)
        try:
            ip = ipaddress.ip_interface(value.strip())
            qs_filter |= Q(ipv6_address__host=str(value))
            qs_filter |= Q(ipv4_address__host=str(value))
        except ValueError:
            pass
        return queryset.filter(qs_filter)


class InternetExchangePeeringSessionFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    autonomous_system__id = django_filters.ModelMultipleChoiceFilter(
        field_name="autonomous_system__id",
        queryset=AutonomousSystem.objects.all(),
        to_field_name="id",
    )
    internet_exchange__id = django_filters.ModelMultipleChoiceFilter(
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
        choices=PLATFORM_CHOICES, null_value=None
    )
    tag = TagFilter()

    class Meta:
        model = Router
        fields = ["name", "hostname"]

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
        method="type_search", choices=ROUTING_POLICY_TYPE_CHOICES, null_value=None
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
        qs_filter = Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        for v in value:
            qs_filter |= Q(type=v)
        return queryset.filter(qs_filter)


class TemplateFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    type = django_filters.MultipleChoiceFilter(
        choices=TEMPLATE_TYPE_CHOICES, null_value=None
    )
    tag = TagFilter()

    class Meta:
        model = Template
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
