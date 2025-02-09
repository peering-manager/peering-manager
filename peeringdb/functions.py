from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Facility, IXLan, NetworkFacility, NetworkIXLan

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from .models import Network

__all__ = (
    "get_possible_peering_sessions",
    "get_shared_facilities",
    "get_shared_internet_exchanges",
)


def get_shared_internet_exchanges(as1: Network, as2: Network) -> QuerySet[IXLan]:
    """
    Returns shared IXPs (via PeeringDB IXLAN objects) between two autonomous systems
    based on PeeringDB data.
    """
    # If both AS are the same or one of each has no PeeringDB record
    # Cannot find shared IXPs
    if as1 is None or as2 is None or as1 == as2:
        return IXLan.objects.none()

    # Find IX LANs to which AS are participating to and get IDs
    ixlan_ids_1 = NetworkIXLan.objects.filter(net=as1).values_list("ixlan", flat=True)
    ixlan_ids_2 = NetworkIXLan.objects.filter(net=as2).values_list("ixlan", flat=True)

    # Return IXP LANs found previously
    return IXLan.objects.filter(pk__in=ixlan_ids_1) & IXLan.objects.filter(
        pk__in=ixlan_ids_2
    )


def get_possible_peering_sessions(
    as1: Network, as2: Network, ixlan: IXLan | None = None
) -> QuerySet[NetworkIXLan]:
    # If both AS are the same or one of each has no PeeringDB record
    # Cannot find sessions for AS1 to peer with AS2
    if as1 is None or as2 is None or as1 == as2:
        return NetworkIXLan.objects.none()

    # Find network IX LANs of AS2 that could be used to peer with AS1
    if ixlan:
        ixlan_ids = NetworkIXLan.objects.filter(net=as1, ixlan=ixlan).values_list(
            "ixlan", flat=True
        )
    else:
        ixlan_ids = NetworkIXLan.objects.filter(net=as1).values_list("ixlan", flat=True)

    return NetworkIXLan.objects.filter(net=as2, ixlan__in=ixlan_ids)


def get_shared_facilities(as1: Network, as2: Network) -> QuerySet[Facility]:
    """
    Returns shared facilities between two autonomous systems based on PeeringDB data.
    """
    # If both AS are the same or one of each has not PeeringDB record
    # Cannot find shared facilities
    if as1 is None or as2 is None or as1 == as2:
        return Facility.objects.none()

    # Find facilities in which AS are located and get IDs
    netfac_ids_1 = NetworkFacility.objects.filter(net=as1).values_list("fac", flat=True)
    netfac_ids_2 = NetworkFacility.objects.filter(net=as2).values_list("fac", flat=True)

    return Facility.objects.filter(pk__in=netfac_ids_1) & Facility.objects.filter(
        pk__in=netfac_ids_2
    )
