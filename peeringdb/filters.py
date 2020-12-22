import ipaddress

import django_filters
from django.db.models import Q

from .models import Network, NetworkContact, NetworkIXLan, Synchronization


class NetworkFilterSet(django_filters.FilterSet):
    class Meta:
        model = Network
        fields = ["asn", "name"]


class NetworkContactFilterSet(django_filters.FilterSet):
    class Meta:
        model = NetworkContact
        fields = ["role", "name", "email", "net_id"]


class NetworkIXLanFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = NetworkIXLan
        fields = ["asn"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        try:
            qs_filter = Q(asn=int(value.strip()))
        except ValueError:
            return queryset

        return queryset.filter(qs_filter)


class SynchronizationFilterSet(django_filters.FilterSet):
    class Meta:
        model = Synchronization
        fields = ["time", "created", "updated", "deleted"]
