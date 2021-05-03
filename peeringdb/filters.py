import ipaddress

import django_filters
from django.db.models import Q

from .models import Network, NetworkContact, NetworkIXLan, Synchronization


class NetworkFilterSet(django_filters.FilterSet):
    class Meta:
        model = Network
        fields = ["id", "asn", "name"]


class NetworkContactFilterSet(django_filters.FilterSet):
    class Meta:
        model = NetworkContact
        fields = ["id", "role", "name", "email", "net_id"]


class NetworkIXLanFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = NetworkIXLan
        fields = ["id", "asn", "net__policy_general"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        try:
            qs_filter = Q(asn__icontains=int(value.strip())) | Q(
                net__name__icontains=value
            )
        except ValueError:
            qs_filter = Q(net__name__icontains=value)

        return queryset.filter(qs_filter)


class SynchronizationFilterSet(django_filters.FilterSet):
    class Meta:
        model = Synchronization
        fields = ["id", "time", "created", "updated", "deleted"]
