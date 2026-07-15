from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.exceptions import NotFound

from peeringdb.models import Network

from ...models import PeeringRequest

if TYPE_CHECKING:
    from uuid import UUID

    from django.db.models import QuerySet

    from ...models import AutonomousSystem


def get_network_or_404(asn: int) -> Network:
    """Returns the cached PeeringDB network for `asn`, raising a 404 if unknown."""
    try:
        return Network.objects.get(asn=asn)
    except Network.DoesNotExist as exc:
        raise NotFound(f"ASN {asn} not found in PeeringDB cache.") from exc


def portal_request_queryset(affiliated: AutonomousSystem) -> QuerySet[PeeringRequest]:
    """Returns the peering requests of `affiliated` with portal serialization prefetches."""
    return (
        PeeringRequest.objects.select_related("local_autonomous_system")
        .prefetch_related(
            "requested_sessions__ixp_connection__internet_exchange_point__peeringdb_ixlan",
            "requested_sessions__peeringdb_facility",
        )
        .filter(local_autonomous_system=affiliated)
    )


def get_peering_request_or_404(affiliated: AutonomousSystem, tracking_id: str | UUID) -> PeeringRequest:
    """Returns the peering request of `affiliated` with `tracking_id`, raising a 404 if unknown."""
    try:
        return portal_request_queryset(affiliated).get(tracking_id=tracking_id)
    except PeeringRequest.DoesNotExist as exc:
        raise NotFound from exc
