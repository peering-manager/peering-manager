from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

import django_filters
from django.db.models import BooleanField, Case, Q, Value, When
from django.utils import timezone

if TYPE_CHECKING:
    from django.db.models import QuerySet

from ..models import HiddenPeer, IXLan, Network

__all__ = ("HiddenPeerFilterSet",)


class HiddenPeerFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    peeringdb_network_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Network.objects.all(), label="PeeringDB Network (ID)"
    )
    peeringdb_network_asn = django_filters.ModelMultipleChoiceFilter(
        field_name="peeringdb_network__asn",
        queryset=Network.objects.all(),
        to_field_name="asn",
        label="PeeringDB Network (ASN)",
    )
    peeringdb_ixlan_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IXLan.objects.all(), label="PeeringDB IXLAN (ID)"
    )
    is_expired = django_filters.BooleanFilter(
        method="is_expired_search", label="Expired"
    )

    class Meta:
        model = HiddenPeer
        fields = ["id", "until"]

    def search(self, queryset: QuerySet, name: str, value: Any) -> QuerySet[HiddenPeer]:
        if not value.strip():
            return queryset

        qs_filter = (
            Q(peeringdb_network__name__icontains=value)
            | Q(peeringdb_ixlan__name__icontains=value)
            | Q(comments__icontains=value)
        )
        with contextlib.suppress(ValueError):
            qs_filter |= Q(peeringdb_network__asn__startswith=int(value.strip()))

        return queryset.filter(qs_filter)

    def is_expired_search(
        self, queryset: QuerySet, name: str, value: Any
    ) -> QuerySet[HiddenPeer]:
        """
        Annotate queryset with an `is_expired` boolean and filter by it.
        """
        qs = queryset.annotate(
            _is_expired=Case(
                When(until__isnull=False, until__lt=timezone.now(), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

        return qs.filter(_is_expired=value)
