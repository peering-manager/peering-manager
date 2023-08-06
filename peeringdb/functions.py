from .models import IXLan, IXLanPrefix, NetworkIXLan

__all__ = ("get_shared_internet_exchanges",)


def get_shared_internet_exchanges(as1, as2):
    """
    Returns shared IXPs (via PeeringDB IXLAN objects) between two autonomous systems
    based on PeeringDB data.
    """
    # If both AS are the same or one of each has not PeeringDB record
    # Cannot find shared IXPs
    if (
        as1 == as2
        or as1 is None
        or as2 is None
        or not as1.peeringdb_network
        or not as2.peeringdb_network
    ):
        return IXLan.objects.none()

    # Find IX LANs to which AS are participating to and get IDs
    ixlan_ids_1 = NetworkIXLan.objects.filter(net=as1.peeringdb_network).values_list(
        "ixlan", flat=True
    )
    ixlan_ids_2 = NetworkIXLan.objects.filter(net=as2.peeringdb_network).values_list(
        "ixlan", flat=True
    )

    # Return IXP LANs found previously
    return IXLan.objects.filter(pk__in=ixlan_ids_1).intersection(
        IXLan.objects.filter(pk__in=ixlan_ids_2)
    )


def get_ixlan_prefixes(ixlan):
    """
    Returns all prefixes used on an IXP LAN.
    """
    if not ixlan or not isinstance(ixlan, IXLan):
        return IXLanPrefix.objects.none()
    return IXLanPrefix.objects.filter(ixlan=ixlan)
