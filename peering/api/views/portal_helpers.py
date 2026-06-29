from __future__ import annotations

import ipaddress
from typing import TYPE_CHECKING

from django.db.models import Q
from rest_framework.exceptions import ValidationError

from net.models import Connection
from peeringdb.models import Facility, IXLan, IXLanPrefix, NetworkIXLan

from ...enums import PeeringRequestType
from ...models import InternetExchange, InternetExchangePeeringSession
from ..constants import IX_LOCATION_PREFIX

if TYPE_CHECKING:
    from peeringdb.models import Network


def _ip_host(value) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    return ipaddress.ip_interface(str(value)).ip


def _format_ip_with_prefix(value, networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network]) -> str:
    host = _ip_host(value)
    for net in networks:
        if host in net:
            return f"{host}/{net.prefixlen}"
    return str(host)


def resolve_location(peer_type: str, location: str) -> tuple[InternetExchange | None, Facility | None]:
    """
    Resolves a portal session `location` identifier into the matching
    `InternetExchange` (for public peering) or `Facility` (for private peering)
    record. Returns a `(ix, facility)` tuple with exactly one populated. Raises
    `ValidationError` on malformed or unknown input.
    """
    if peer_type == PeeringRequestType.PUBLIC_PEERING:
        if not location.startswith(IX_LOCATION_PREFIX):
            raise ValidationError({"location": f"Public peering location must use '{IX_LOCATION_PREFIX}<id>' format."})

        try:
            ixlan = IXLan.objects.get(pk=int(location.removeprefix(IX_LOCATION_PREFIX)))
        except (ValueError, IXLan.DoesNotExist) as exc:
            raise ValidationError({"location": f"Unknown IX: {location!r}."}) from exc

        ix = InternetExchange.objects.filter(peeringdb_ixlan=ixlan).first()
        if ix is None:
            raise ValidationError({"location": f"IX {location!r} not found."})

        return ix, None

    # If not public, then we are in a private peering context
    if not location:
        raise ValidationError({"location": "Private peering requires a facility location."})

    try:
        facility = Facility.objects.get(pk=int(location))
    except (ValueError, Facility.DoesNotExist) as exc:
        raise ValidationError({"location": f"Unknown facility: {location!r}."}) from exc

    return None, facility


def resolve_peer_connection(ixp: InternetExchange, peer_ip: str) -> Connection:
    """
    Finds the `Connection` at `ix` whose IPv4 or IPv6 address matches `peer_ip`.
    The match is on host address only, prefix length differences are tolerated.
    """
    if not peer_ip:
        raise ValidationError({"peer_ip": "Required for public peering."})

    try:
        host = str(ipaddress.ip_interface(peer_ip).ip)
    except ValueError as exc:
        raise ValidationError({"peer_ip": f"Not a valid IP address: {peer_ip!r}."}) from exc

    conn = (
        Connection.objects.filter(internet_exchange_point=ixp)
        .filter(Q(ipv4_address__host=host) | Q(ipv6_address__host=host))
        .first()
    )
    if conn is None:
        raise ValidationError({"peer_ip": f"Unknown peer IP {peer_ip!r} at this IXP."})

    return conn


def session_proposals(ixp: InternetExchange, peer_network: Network) -> list[dict]:
    """
    Returns the list of BGP session proposals with `peer_network` on `ixp`.

    A session is uniquely identified by `(connection, peer_ip)`, and both sides can
    have several IPs on the same IXLan, so this returns the cartesian product per
    address family. Each entry is:

    * `local_ip`: peer's IP on this IX (PeeringDB) with prefix length.
    * `peer_ip`: a single IP from a configured `Connection`.
    * `address_family`: 4 or 6.
    * `existing`: whether an `InternetExchangePeeringSession` already uses this
      `(connection, peer_ip)` pair.

    Rows are skipped when no connection exists for the address family. Returns an
    empty list if the IXP is not linked to a PeeringDB record.
    """
    if not ixp.peeringdb_ixlan:
        return []

    peer_netixlans = NetworkIXLan.objects.filter(net=peer_network, ixlan=ixp.peeringdb_ixlan)

    # Group connections by AF (one IXP can have several)
    connections: dict[int, list[tuple[int, str]]] = {4: [], 6: []}
    for connection_id, ipv4, ipv6 in Connection.objects.filter(internet_exchange_point=ixp).values_list(
        "id", "ipv4_address", "ipv6_address"
    ):
        if ipv4 is not None:
            connections[4].append((connection_id, str(ipv4)))
        if ipv6 is not None:
            connections[6].append((connection_id, str(ipv6)))

    # IXLan prefixes used to attach the right netmask to PeeringDB IPs, which are
    # stored bare on netixlan.
    ixlan_networks: dict[int, list] = {4: [], 6: []}
    for prefix in IXLanPrefix.objects.filter(ixlan=ixp.peeringdb_ixlan):
        net = ipaddress.ip_network(str(prefix.prefix))
        ixlan_networks[net.version].append(net)

    existing_pairs = {
        (connection_id, str(_ip_host(ip)))
        for connection_id, ip in InternetExchangePeeringSession.objects.filter(
            ixp_connection__internet_exchange_point=ixp
        ).values_list("ixp_connection_id", "ip_address")
    }

    proposals: list[dict] = []
    for netixlan in peer_netixlans:
        for ip, af in ((netixlan.ipaddr4, 4), (netixlan.ipaddr6, 6)):
            if ip is None:
                continue
            conns = connections.get(af, [])
            if not conns:
                continue
            peer_ip_host = str(_ip_host(ip))
            local_ip = _format_ip_with_prefix(ip, ixlan_networks.get(af, []))
            for conn_id, conn_ip in conns:
                proposals.append(
                    {
                        "local_ip": local_ip,
                        "peer_ip": conn_ip,
                        "address_family": af,
                        "existing": (conn_id, peer_ip_host) in existing_pairs,
                    }
                )
    return proposals
