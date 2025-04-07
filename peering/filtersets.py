import contextlib
import ipaddress

import django_filters
from django.db.models import Q

from bgp.models import Relationship
from devices.models import Router
from net.models import BFD, Connection
from peering_manager.filtersets import (
    OrganisationalModelFilterSet,
    PeeringManagerModelFilterSet,
)

from .enums import (
    BGPGroupStatus,
    BGPSessionStatus,
    BGPState,
    CommunityType,
    RoutingPolicyType,
)
from .models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)


class AutonomousSystemFilterSet(PeeringManagerModelFilterSet):
    class Meta:
        model = AutonomousSystem
        fields = [
            "id",
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
            | Q(description__icontains=value)
            | Q(irr_as_set__icontains=value)
        )
        with contextlib.suppress(ValueError):
            qs_filter |= Q(asn=int(value.strip()))

        return queryset.filter(qs_filter)


class BGPGroupFilterSet(OrganisationalModelFilterSet):
    status = django_filters.MultipleChoiceFilter(choices=BGPGroupStatus, null_value="")

    class Meta:
        model = BGPGroup
        fields = ["id"]


class CommunityFilterSet(PeeringManagerModelFilterSet):
    type = django_filters.MultipleChoiceFilter(choices=CommunityType, null_value="")

    class Meta:
        model = Community
        fields = ["id", "value", "type"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(value__icontains=value)
            | Q(slug__icontains=value)
            | Q(description__icontains=value)
        )


class DirectPeeringSessionFilterSet(PeeringManagerModelFilterSet):
    local_autonomous_system_id = django_filters.ModelMultipleChoiceFilter(
        queryset=AutonomousSystem.objects.defer("prefixes"), label="Local AS (ID)"
    )
    local_autonomous_system_asn = django_filters.ModelMultipleChoiceFilter(
        field_name="local_autonomous_system__asn",
        queryset=AutonomousSystem.objects.defer("prefixes"),
        to_field_name="asn",
        label="Local AS (ASN)",
    )
    local_autonomous_system = django_filters.ModelMultipleChoiceFilter(
        field_name="local_autonomous_system__name",
        queryset=AutonomousSystem.objects.defer("prefixes"),
        to_field_name="name",
        label="Local AS (Name)",
    )
    autonomous_system_id = django_filters.ModelMultipleChoiceFilter(
        queryset=AutonomousSystem.objects.defer("prefixes"), label="Remote AS (ID)"
    )
    autonomous_system_asn = django_filters.ModelMultipleChoiceFilter(
        field_name="autonomous_system__asn",
        queryset=AutonomousSystem.objects.defer("prefixes"),
        to_field_name="asn",
        label="Remote AS (ASN)",
    )
    autonomous_system = django_filters.ModelMultipleChoiceFilter(
        field_name="autonomous_system__name",
        queryset=AutonomousSystem.objects.defer("prefixes"),
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
    status = django_filters.MultipleChoiceFilter(
        choices=BGPSessionStatus, null_value=""
    )
    bfd_id = django_filters.ModelMultipleChoiceFilter(
        queryset=BFD.objects.all(), label="BFD (ID)"
    )
    bfd = django_filters.ModelMultipleChoiceFilter(
        field_name="bfd__name",
        queryset=BFD.objects.all(),
        to_field_name="name",
        label="BFD (Name)",
    )
    relationship_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Relationship.objects.all(), label="Relationship (ID)"
    )
    relationship = django_filters.ModelMultipleChoiceFilter(
        field_name="relationship__name",
        queryset=Relationship.objects.all(),
        to_field_name="name",
        label="Relationship (Name)",
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
    connection_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Connection.objects.all(), label="Connection (ID)"
    )
    bgp_state = django_filters.MultipleChoiceFilter(choices=BGPState, null_value="")

    class Meta:
        model = DirectPeeringSession
        fields = ["id", "multihop_ttl", "passive"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(service_reference__icontains=value)
            | Q(comments__icontains=value)
            | Q(autonomous_system__name__icontains=value)
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


class InternetExchangeFilterSet(OrganisationalModelFilterSet):
    status = django_filters.MultipleChoiceFilter(choices=BGPGroupStatus, null_value="")
    local_autonomous_system_id = django_filters.ModelMultipleChoiceFilter(
        queryset=AutonomousSystem.objects.defer("prefixes"), label="Local AS (ID)"
    )
    local_autonomous_system_asn = django_filters.ModelMultipleChoiceFilter(
        field_name="local_autonomous_system__asn",
        queryset=AutonomousSystem.objects.defer("prefixes"),
        to_field_name="asn",
        label="Local AS (ASN)",
    )
    local_autonomous_system = django_filters.ModelMultipleChoiceFilter(
        field_name="local_autonomous_system__name",
        queryset=AutonomousSystem.objects.defer("prefixes"),
        to_field_name="name",
        label="Local AS (Name)",
    )

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
        with contextlib.suppress(ValueError):
            qs_filter |= Q(local_autonomous_system__asn=int(value.strip()))
        return queryset.filter(qs_filter)


class InternetExchangePeeringSessionFilterSet(PeeringManagerModelFilterSet):
    autonomous_system_id = django_filters.ModelMultipleChoiceFilter(
        queryset=AutonomousSystem.objects.defer("prefixes"), label="Remote AS (ID)"
    )
    autonomous_system_asn = django_filters.ModelMultipleChoiceFilter(
        field_name="autonomous_system__asn",
        queryset=AutonomousSystem.objects.defer("prefixes"),
        to_field_name="asn",
        label="Remote AS (ASN)",
    )
    autonomous_system = django_filters.ModelMultipleChoiceFilter(
        field_name="autonomous_system__name",
        queryset=AutonomousSystem.objects.defer("prefixes"),
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
    bfd_id = django_filters.ModelMultipleChoiceFilter(
        queryset=BFD.objects.all(), label="BFD (ID)"
    )
    bfd = django_filters.ModelMultipleChoiceFilter(
        field_name="bfd__name",
        queryset=BFD.objects.all(),
        to_field_name="name",
        label="BFD (Name)",
    )
    address_family = django_filters.NumberFilter(method="address_family_search")
    status = django_filters.MultipleChoiceFilter(
        choices=BGPSessionStatus, null_value=""
    )
    bgp_state = django_filters.MultipleChoiceFilter(choices=BGPState, null_value="")

    class Meta:
        model = InternetExchangePeeringSession
        fields = ["id", "multihop_ttl", "passive", "is_route_server"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(service_reference__icontains=value)
            | Q(comments__icontains=value)
            | Q(autonomous_system__name__icontains=value)
            | Q(ixp_connection__router__name__icontains=value)
            | Q(ixp_connection__router__hostname__icontains=value)
            | Q(ixp_connection__internet_exchange_point__name__icontains=value)
            | Q(ixp_connection__internet_exchange_point__slug__icontains=value)
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


class RoutingPolicyFilterSet(OrganisationalModelFilterSet):
    type = django_filters.MultipleChoiceFilter(
        method="type_search", choices=RoutingPolicyType, null_value=None
    )

    class Meta:
        model = RoutingPolicy
        fields = ["id", "weight", "address_family"]

    def type_search(self, queryset, name, value):
        qs_filter = Q(type=RoutingPolicyType.IMPORT_EXPORT)
        for v in value:
            qs_filter |= Q(type=v)
        return queryset.filter(qs_filter)
