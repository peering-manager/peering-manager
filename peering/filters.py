import ipaddress

import django_filters
from django.db.models import Q

from devices.models import Platform
from net.models import Connection
from utils.filters import (
    BaseFilterSet,
    CreatedUpdatedFilterSet,
    NameSlugSearchFilterSet,
    TagFilter,
)

from .enums import BGPRelationship, CommunityType, DeviceState, RoutingPolicyType
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


class AutonomousSystemFilterSet(BaseFilterSet, CreatedUpdatedFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    tag = TagFilter()

    class Meta:
        model = AutonomousSystem
        fields = ["id", "asn", "ipv6_max_prefixes", "ipv4_max_prefixes", "affiliated"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(irr_as_set__icontains=value)
        )


class BGPGroupFilterSet(
    BaseFilterSet, CreatedUpdatedFilterSet, NameSlugSearchFilterSet
):
    q = django_filters.CharFilter(method="search", label="Search")
    tag = TagFilter()

    class Meta:
        model = BGPGroup
        fields = ["id"]


class CommunityFilterSet(
    BaseFilterSet, CreatedUpdatedFilterSet, NameSlugSearchFilterSet
):
    type = django_filters.MultipleChoiceFilter(
        choices=CommunityType.choices, null_value=None
    )
    tag = TagFilter()

    class Meta:
        model = Community
        fields = ["id", "value", "type"]


class ConfigurationFilterSet(BaseFilterSet, CreatedUpdatedFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    tag = TagFilter()

    class Meta:
        model = Configuration
        fields = ["id"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(Q(name__icontains=value) | Q(template__icontains=value))


class DirectPeeringSessionFilterSet(BaseFilterSet, CreatedUpdatedFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    local_autonomous_system_id = django_filters.ModelMultipleChoiceFilter(
        queryset=AutonomousSystem.objects.all(),
        label="Local AS (ID)",
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
    autonomous_system_id = django_filters.ModelMultipleChoiceFilter(
        queryset=AutonomousSystem.objects.all(), label="Remote AS (ID)"
    )
    autonomous_system_asn = django_filters.ModelMultipleChoiceFilter(
        field_name="autonomous_system__asn",
        queryset=AutonomousSystem.objects.all(),
        to_field_name="asn",
        label="Remote AS (ASN)",
    )
    autonomous_system = django_filters.ModelMultipleChoiceFilter(
        field_name="autonomous_system__name",
        queryset=AutonomousSystem.objects.all(),
        to_field_name="name",
        label="Remote AS (Name)",
    )
    bgp_group_id = django_filters.ModelMultipleChoiceFilter(
        queryset=BGPGroup.objects.all(), label="BGP Group (ID)"
    )
    bgp_group = django_filters.ModelMultipleChoiceFilter(
        field_name="bgp_group__name",
        queryset=BGPGroup.objects.all(),
        to_field_name="name",
        label="BGP Group (Name)",
    )
    address_family = django_filters.NumberFilter(method="address_family_search")
    relationship = django_filters.MultipleChoiceFilter(
        choices=BGPRelationship.choices, null_value=None
    )
    router_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Router.objects.all(), label="Router (ID)"
    )
    router_name = django_filters.ModelMultipleChoiceFilter(
        field_name="router__name",
        queryset=Router.objects.all(),
        to_field_name="name",
        label="Router (Name)",
    )
    router = django_filters.ModelMultipleChoiceFilter(
        field_name="router__hostname",
        queryset=Router.objects.all(),
        to_field_name="hostname",
        label="Router (Hostname)",
    )
    tag = TagFilter()

    class Meta:
        model = DirectPeeringSession
        fields = ["id", "multihop_ttl", "enabled"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(autonomous_system__name__icontains=value)
            | Q(bgp_group__name__icontains=value)
            | Q(bgp_group__slug__icontains=value)
            | Q(router__name__icontains=value)
            | Q(router__hostname__icontains=value)
        )
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


class EmailFilterSet(BaseFilterSet, CreatedUpdatedFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    tag = TagFilter()

    class Meta:
        model = Email
        fields = ["id"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(subject__icontains=value)
            | Q(template__icontains=value)
        )


class InternetExchangeFilterSet(BaseFilterSet, CreatedUpdatedFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
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
    tag = TagFilter()

    class Meta:
        model = InternetExchange
        fields = ["id"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(slug__icontains=value)
            | Q(local_autonomous_system__name__icontains=value)
        )
        try:
            qs_filter |= Q(local_autonomous_system__asn=int(value.strip()))
        except ValueError:
            pass
        return queryset.filter(qs_filter)


class InternetExchangePeeringSessionFilterSet(BaseFilterSet, CreatedUpdatedFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    autonomous_system_id = django_filters.ModelMultipleChoiceFilter(
        queryset=AutonomousSystem.objects.all(), label="Remote AS (ID)"
    )
    autonomous_system_asn = django_filters.ModelMultipleChoiceFilter(
        field_name="autonomous_system__asn",
        queryset=AutonomousSystem.objects.all(),
        to_field_name="asn",
        label="Remote AS (ASN)",
    )
    autonomous_system = django_filters.ModelMultipleChoiceFilter(
        field_name="autonomous_system__name",
        queryset=AutonomousSystem.objects.all(),
        to_field_name="name",
        label="Remote AS (Name)",
    )
    ixp_connection_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Connection.objects.all(), label="IXP Connection (ID)"
    )
    internet_exchange_id = django_filters.ModelMultipleChoiceFilter(
        field_name="ixp_connection__internet_exchange_point",
        queryset=InternetExchange.objects.all(),
        label="IX (ID)",
    )
    internet_exchange = django_filters.ModelMultipleChoiceFilter(
        field_name="ixp_connection__internet_exchange_point__name",
        queryset=InternetExchange.objects.all(),
        to_field_name="name",
        label="IX (Name)",
    )
    address_family = django_filters.NumberFilter(method="address_family_search")
    tag = TagFilter()

    class Meta:
        model = InternetExchangePeeringSession
        fields = ["id", "multihop_ttl", "enabled", "is_route_server"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(autonomous_system__name__icontains=value)
            | Q(internet_exchange__name__icontains=value)
            | Q(internet_exchange__slug__icontains=value)
            | Q(internet_exchange__router__name__icontains=value)
            | Q(internet_exchange__router__hostname__icontains=value)
        )
        try:
            ip = ipaddress.ip_interface(value.strip())
            qs_filter |= Q(ip_address__host=str(ip))
        except ValueError:
            pass
        return queryset.filter(qs_filter)

    def address_family_search(self, queryset, name, value):
        if value in [4, 6]:
            return queryset.filter(Q(ip_address__family=value))
        return queryset


class RouterFilterSet(BaseFilterSet, CreatedUpdatedFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
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
    configuration_template_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Configuration.objects.all(), label="Configuration (ID)"
    )
    configuration_template = django_filters.ModelMultipleChoiceFilter(
        field_name="configuration_template__name",
        queryset=Configuration.objects.all(),
        to_field_name="name",
        label="Configuration (Name)",
    )
    device_state = django_filters.MultipleChoiceFilter(
        choices=DeviceState.choices, null_value=None
    )
    tag = TagFilter()

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


class RoutingPolicyFilterSet(
    BaseFilterSet, CreatedUpdatedFilterSet, NameSlugSearchFilterSet
):
    type = django_filters.MultipleChoiceFilter(
        method="type_search", choices=RoutingPolicyType.choices, null_value=None
    )
    tag = TagFilter()

    class Meta:
        model = RoutingPolicy
        fields = ["id", "weight", "address_family"]

    def type_search(self, queryset, name, value):
        qs_filter = Q(type=RoutingPolicyType.IMPORT_EXPORT)
        for v in value:
            qs_filter |= Q(type=v)
        return queryset.filter(qs_filter)
