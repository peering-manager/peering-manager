import ipaddress

import django_filters
from django.db.models import Q

from devices.models import Router
from peering.models import InternetExchange
from peering_manager.filtersets import PeeringManagerModelFilterSet

from ..enums import ConnectionStatus
from ..models import Connection

__all__ = ("ConnectionFilterSet",)


class ConnectionFilterSet(PeeringManagerModelFilterSet):
    status = django_filters.MultipleChoiceFilter(
        choices=ConnectionStatus, null_value=None
    )
    internet_exchange_point_id = django_filters.ModelMultipleChoiceFilter(
        queryset=InternetExchange.objects.all(), label="IXP (ID)"
    )
    internet_exchange_point = django_filters.ModelMultipleChoiceFilter(
        field_name="internet_exchange_point__name",
        queryset=InternetExchange.objects.all(),
        to_field_name="name",
        label="IXP (Name)",
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

    class Meta:
        model = Connection
        fields = ["id", "vlan"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(interface__icontains=value)
            | Q(description__icontains=value)
            | Q(router__name__icontains=value)
            | Q(router__hostname__icontains=value)
        )
        try:
            ip = ipaddress.ip_interface(value.strip())
            qs_filter |= Q(ipv6_address__host=str(ip)) | Q(ipv4_address__host=str(ip))
        except ValueError:
            pass
        return queryset.filter(qs_filter)
