from .models import IXLan, IXLanPrefix, NetworkIXLan


def get_shared_internet_exchanges(as1, as2):
    """
    Returns shared IXPs between two autonomous systems based on PeeringDB data.

    TODO: rewrite this using QuerySet.intersection()
    """
    # If both AS are the same, no point in sharing IXPs
    if as1 == as2 or as1 is None or as2 is None:
        return []

    # Find IX LANs to which AS are participating to
    ixlans1 = [n.ixlan for n in NetworkIXLan.objects.filter(net=as1.peeringdb_network)]
    ixlans2 = [n.ixlan for n in NetworkIXLan.objects.filter(net=as2.peeringdb_network)]

    # Keep only shared LANs
    shared_ixlans = list(set(ixlans1).intersection(ixlans2))

    # Return IXPs given the LANs found previously
    return [ixlan.ix for ixlan in shared_ixlans]


def get_ixlan_prefixes(ixlan):
    """
    Returns all prefixes used on an IXP LAN.
    """
    if not ixlan or not isinstance(ixlan, IXLan):
        return []
    return IXLanPrefix.objects.filter(ixlan=ixlan)
