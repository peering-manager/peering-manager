import ipaddress

from django.db.models import Q

import django_filters

from .constants import BGP_RELATIONSHIP_CHOICES, PLATFORM_CHOICES
from .models import (
    AutonomousSystem,
    Community,
    ConfigurationTemplate,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from peeringdb.models import PeerRecord


class AutonomousSystemFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = AutonomousSystem
        fields = ["asn", "name", "irr_as_set", "ipv6_max_prefixes", "ipv4_max_prefixes"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(irr_as_set__icontains=value)
            | Q(comment__icontains=value)
        )
        try:
            qs_filter |= Q(asn=int(value.strip()))
            qs_filter |= Q(ipv6_max_prefixes=int(value.strip()))
            qs_filter |= Q(ipv4_max_prefixes=int(value.strip()))
        except ValueError:
            pass
        return queryset.filter(qs_filter)


class CommunityFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = Community
        fields = ["name", "value", "type"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(value__icontains=value)
            | Q(type__icontains=value)
            | Q(comment__icontains=value)
        )
        return queryset.filter(qs_filter)


class ConfigurationTemplateFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = ConfigurationTemplate
        fields = ["name"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value) | Q(template__icontains=value)
        return queryset.filter(qs_filter)


class DirectPeeringSessionFilter(django_filters.FilterSet):
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

    class Meta:
        model = DirectPeeringSession
        fields = ["local_asn", "multihop_ttl", "enabled"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(relationship__icontains=value) | Q(comment__icontains=value)
        try:
            ip = ipaddress.ip_interface(value.strip())
            qs_filter |= Q(ip_address__host=str(ip))
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


class InternetExchangeFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    configuration_template = django_filters.ModelMultipleChoiceFilter(
        field_name="configuration_template__id",
        queryset=ConfigurationTemplate.objects.all(),
        to_field_name="id",
        label="Template",
    )
    router = django_filters.ModelMultipleChoiceFilter(
        field_name="router__id",
        queryset=Router.objects.all(),
        to_field_name="id",
        label="Router",
    )

    class Meta:
        model = InternetExchange
        fields = ["name"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value) | Q(comment__icontains=value)
        try:
            ip = ipaddress.ip_interface(value.strip())
            qs_filter |= Q(ipv6_address__host=str(value))
            qs_filter |= Q(ipv4_address__host=str(value))
        except ValueError:
            pass
        return queryset.filter(qs_filter)


class InternetExchangePeeringSessionFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    address_family = django_filters.NumberFilter(method="address_family_search")

    class Meta:
        model = InternetExchangePeeringSession
        fields = [
            "multihop_ttl",
            "enabled",
            "is_route_server",
            "autonomous_system__asn",
            "autonomous_system__name",
            "internet_exchange__name",
            "internet_exchange__slug",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(autonomous_system__name__icontains=value)
            | Q(internet_exchange__name__icontains=value)
            | Q(internet_exchange__slug__icontains=value)
            | Q(comment__icontains=value)
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


class PeerRecordFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = PeerRecord
        fields = [
            "network__asn",
            "network__name",
            "network__irr_as_set",
            "network__info_prefixes6",
            "network__info_prefixes4",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(network__name__icontains=value) | Q(
            network__irr_as_set__icontains=value
        )
        try:
            ip = ipaddress.ip_interface(value.strip())
            qs_filter |= Q(network_ixlan__ipaddr6__host=str(ip))
            qs_filter |= Q(network_ixlan__ipaddr4__host=str(ip))
        except ValueError:
            pass
        try:
            qs_filter |= Q(network__asn=int(value.strip()))
            qs_filter |= Q(network__info_prefixes6=int(value.strip()))
            qs_filter |= Q(network__info_prefixes4=int(value.strip()))
        except ValueError:
            pass
        return queryset.filter(qs_filter)


class RouterFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    platform = django_filters.MultipleChoiceFilter(
        choices=PLATFORM_CHOICES, null_value=None
    )

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
            | Q(comment__icontains=value)
        )
        return queryset.filter(qs_filter)


class RoutingPolicyFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = RoutingPolicy
        fields = ["name", "type", "weight"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(type__icontains=value)
            | Q(comment__icontains=value)
        )
        return queryset.filter(qs_filter)
