import ipaddress

import django_filters
from django.db.models import Q

from .models import Network, NetworkContact, NetworkIXLan, Synchronisation


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
        fields = [
            "id",
            "asn",
            "is_rs_peer",
            "net__info_traffic",
            "net__info_scope",
            "net__info_type",
            "net__policy_general",
            "net__policy_locations",
            "net__policy_ratio",
            "net__policy_contracts",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(net__name__icontains=value)
        try:
            qs_filter |= Q(asn=int(value.strip()))
        except ValueError:
            pass

        return queryset.filter(qs_filter)


class SynchronisationFilterSet(django_filters.FilterSet):
    class Meta:
        model = Synchronisation
        fields = ["id", "time", "created", "updated", "deleted"]
