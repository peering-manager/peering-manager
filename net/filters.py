import ipaddress

import django_filters
from django.db.models import Q

from peering.models import InternetExchange, Router
from utils.filters import BaseFilterSet, CreatedUpdatedFilterSet, TagFilter

from .models import Connection


class ConnectionFilterSet(BaseFilterSet, CreatedUpdatedFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
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
    tag = TagFilter()

    class Meta:
        model = Connection
        fields = ["id", "vlan"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        try:
            ip = ipaddress.ip_interface(value.strip())
            qs_filter = Q(ipv6_address__host=str(ip)) | Q(ipv4_address__host=str(ip))
        except ValueError:
            pass
        return queryset.filter(qs_filter)
