from __future__ import annotations

import contextlib
import ipaddress
from typing import TYPE_CHECKING, Any

import django_filters
from django.db.models import Q

if TYPE_CHECKING:
    from django.db.models import QuerySet

from ..models import (
    Campus,
    Facility,
    InternetExchange,
    InternetExchangeFacility,
    IXLan,
    IXLanPrefix,
    Network,
    NetworkContact,
    NetworkFacility,
    NetworkIXLan,
    Organization,
    Synchronisation,
)

__all__ = (
    "CampusFilterSet",
    "FacilityFilterSet",
    "IXLanFilterSet",
    "IXLanPrefixFilterSet",
    "InternetExchangeFacilityFilterSet",
    "InternetExchangeFilterSet",
    "NetworkContactFilterSet",
    "NetworkFacilityFilterSet",
    "NetworkFilterSet",
    "NetworkIXLanFilterSet",
    "OrganizationFilterSet",
    "SynchronisationFilterSet",
)


class CampusFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    org_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Organization.objects.all(), label="Org (ID)"
    )

    class Meta:
        model = Campus
        fields = ["id", "name"]

    def search(self, queryset: QuerySet, name: str, value: Any) -> QuerySet[Campus]:
        if not value.strip():
            return queryset

        return queryset.filter(Q(name__icontains=value))


class FacilityFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    org_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Organization.objects.all(), label="Org (ID)"
    )

    class Meta:
        model = Facility
        fields = ["id", "name"]

    def search(self, queryset: QuerySet, name: str, value: Any) -> QuerySet[Facility]:
        if not value.strip():
            return queryset

        return queryset.filter(Q(name__icontains=value))


class InternetExchangeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    org_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Organization.objects.all(), label="Org (ID)"
    )

    class Meta:
        model = InternetExchange
        fields = ["id", "name"]

    def search(
        self, queryset: QuerySet, name: str, value: Any
    ) -> QuerySet[InternetExchange]:
        if not value.strip():
            return queryset

        return queryset.filter(Q(name__icontains=value))


class InternetExchangeFacilityFilterSet(django_filters.FilterSet):
    fac_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Facility.objects.all(), label="Fac (ID)"
    )
    ix_id = django_filters.ModelMultipleChoiceFilter(
        queryset=InternetExchange.objects.all(), label="IX (ID)"
    )

    class Meta:
        model = InternetExchangeFacility
        fields = ["id"]


class IXLanFilterSet(django_filters.FilterSet):
    ix_id = django_filters.ModelMultipleChoiceFilter(
        queryset=InternetExchange.objects.all(), label="IX (ID)"
    )

    class Meta:
        model = IXLan
        fields = ["id", "vlan", "rs_asn"]


class IXLanPrefixFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    ixlan_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IXLan.objects.all(), label="IXLan (ID)"
    )

    class Meta:
        model = IXLanPrefix
        fields = ["id", "in_dfz"]

    def search(
        self, queryset: QuerySet, name: str, value: Any
    ) -> QuerySet[IXLanPrefix]:
        if not value.strip():
            return queryset

        try:
            prefix = ipaddress.ip_network(value.strip())
            return queryset.filter(Q(prefix=prefix))
        except ValueError:
            pass

        return queryset


class NetworkFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    org_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Organization.objects.all(), label="Org (ID)"
    )

    class Meta:
        model = Network
        fields = ["id", "asn", "name"]

    def search(self, queryset: QuerySet, name: str, value: Any) -> QuerySet[Network]:
        if not value.strip():
            return queryset

        qs_filter = Q(name__icontains=value) | Q(irr_as_set__icontains=value)
        with contextlib.suppress(ValueError):
            qs_filter |= Q(asn=int(value.strip()))

        return queryset.filter(qs_filter)


class NetworkContactFilterSet(django_filters.FilterSet):
    net_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Network.objects.all(), label="Network (ID)"
    )
    net_asn = django_filters.ModelMultipleChoiceFilter(
        field_name="net__asn",
        queryset=Network.objects.all(),
        to_field_name="asn",
        label="Network (ASN)",
    )

    class Meta:
        model = NetworkContact
        fields = ["id", "role", "name", "email"]


class NetworkFacilityFilterSet(django_filters.FilterSet):
    fac_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Facility.objects.all(), label="Fac (ID)"
    )
    net_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Network.objects.all(), label="Network (ID)"
    )

    class Meta:
        model = NetworkFacility
        fields = ["id", "local_asn"]


class NetworkIXLanFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    net_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Network.objects.all(), label="Network (ID)"
    )
    net_asn = django_filters.ModelMultipleChoiceFilter(
        field_name="net__asn",
        queryset=Network.objects.all(),
        to_field_name="asn",
        label="Network (ASN)",
    )
    ixlan_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IXLan.objects.all(), label="IXLan (ID)"
    )

    class Meta:
        model = NetworkIXLan
        fields = [
            "id",
            "asn",
            "is_rs_peer",
            "bfd_support",
            "net__info_traffic",
            "net__info_scope",
            "net__info_type",
            "net__policy_general",
            "net__policy_locations",
            "net__policy_ratio",
            "net__policy_contracts",
        ]

    def search(
        self, queryset: QuerySet, name: str, value: Any
    ) -> QuerySet[NetworkIXLan]:
        if not value.strip():
            return queryset

        qs_filter = Q(net__name__icontains=value)
        with contextlib.suppress(ValueError):
            qs_filter |= Q(asn=int(value.strip()))
        try:
            ip = ipaddress.ip_address(value.strip())
            if ip.version == 6:
                qs_filter |= Q(ipaddr6__host=str(ip))
            else:
                qs_filter |= Q(ipaddr4__host=str(ip))
        except ValueError:
            pass

        return queryset.filter(qs_filter)


class OrganizationFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = Organization
        fields = ["id", "name"]

    def search(
        self, queryset: QuerySet, name: str, value: Any
    ) -> QuerySet[Organization]:
        if not value.strip():
            return queryset

        return queryset.filter(Q(name__icontains=value))


class SynchronisationFilterSet(django_filters.FilterSet):
    class Meta:
        model = Synchronisation
        fields = ["id", "time", "created", "updated", "deleted"]
