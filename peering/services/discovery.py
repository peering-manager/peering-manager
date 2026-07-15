from __future__ import annotations

import ipaddress
from typing import TYPE_CHECKING, Protocol

from net.models import Connection
from peeringdb.models import IXLanPrefix, NetworkIXLan

from ..constants import format_facility_location, format_ix_location
from ..enums import PeeringRequestType
from ..functions import ip_host
from ..models import InternetExchangePeeringSession

if TYPE_CHECKING:
    from collections.abc import Sequence

    from peeringdb.models import Network

    from ..models import AutonomousSystem, InternetExchange

__all__ = (
    "LocationDiscoveryService",
    "MutualLocationProvider",
    "PrivateLocationProvider",
    "PublicLocationProvider",
    "build_location_discovery_service",
)


def _format_ip_with_prefix(value, networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network]) -> str:
    host = ip_host(value)
    for net in networks:
        if host in net:
            return f"{host}/{net.prefixlen}"
    return str(host)


def session_proposals_by_ixp(ixps: Sequence[InternetExchange], peer_network: Network) -> dict[int, list[dict]]:
    """
    Returns the BGP session proposals with `peer_network` for each IXP, keyed by IXP primary key, with a constant
    number of queries no matter how many IXPs are given.

    A session is uniquely identified by `(connection, peer_ip)`, and both sides can have several IPs on the same
    IXLan, so proposals are the cartesian product per address family. Each entry is:

    * `local_ip`: peer's IP on this IX (PeeringDB) with prefix length.
    * `peer_ip`: a single IP from a configured `Connection`.
    * `address_family`: 4 or 6.
    * `existing`: whether an `InternetExchangePeeringSession` already uses this `(connection, peer_ip)` pair.

    Rows are skipped when no connection exists for the address family. An IXP not linked to a PeeringDB record gets
    an empty list.
    """
    ixps = list(ixps)
    linked = [ixp for ixp in ixps if ixp.peeringdb_ixlan_id]
    ixlan_ids = {ixp.peeringdb_ixlan_id for ixp in linked}

    netixlans: dict[int, list[NetworkIXLan]] = {}
    for netixlan in NetworkIXLan.objects.filter(net=peer_network, ixlan_id__in=ixlan_ids):
        netixlans.setdefault(netixlan.ixlan_id, []).append(netixlan)

    # One IXP can have several connections, each with a v4 and/or v6 address
    connections: dict[int, dict[int, list[tuple[int, str]]]] = {}
    for ixp_id, connection_id, ipv4, ipv6 in Connection.objects.filter(internet_exchange_point__in=linked).values_list(
        "internet_exchange_point_id", "id", "ipv4_address", "ipv6_address"
    ):
        by_af = connections.setdefault(ixp_id, {4: [], 6: []})
        if ipv4 is not None:
            by_af[4].append((connection_id, str(ipv4)))
        if ipv6 is not None:
            by_af[6].append((connection_id, str(ipv6)))

    # IXLan prefixes used to attach the right netmask to PeeringDB IPs, which are stored bare on netixlan
    ixlan_networks: dict[int, dict[int, list]] = {}
    for ixlan_id, prefix in IXLanPrefix.objects.filter(ixlan_id__in=ixlan_ids).values_list("ixlan_id", "prefix"):
        net = ipaddress.ip_network(str(prefix))
        ixlan_networks.setdefault(ixlan_id, {4: [], 6: []})[net.version].append(net)

    existing_pairs = {
        (connection_id, str(ip_host(ip)))
        for connection_id, ip in InternetExchangePeeringSession.objects.filter(
            ixp_connection__internet_exchange_point__in=linked
        ).values_list("ixp_connection_id", "ip_address")
    }

    proposals: dict[int, list[dict]] = {ixp.pk: [] for ixp in ixps}
    for ixp in linked:
        entries = proposals[ixp.pk]
        ixp_connections = connections.get(ixp.pk, {})
        networks = ixlan_networks.get(ixp.peeringdb_ixlan_id, {})
        for netixlan in netixlans.get(ixp.peeringdb_ixlan_id, []):
            for ip, af in ((netixlan.ipaddr4, 4), (netixlan.ipaddr6, 6)):
                if ip is None:
                    continue
                conns = ixp_connections.get(af, [])
                if not conns:
                    continue
                peer_ip_host = str(ip_host(ip))
                local_ip = _format_ip_with_prefix(ip, networks.get(af, []))
                for conn_id, conn_ip in conns:
                    entries.append(
                        {
                            "local_ip": local_ip,
                            "peer_ip": conn_ip,
                            "address_family": af,
                            "existing": (conn_id, peer_ip_host) in existing_pairs,
                        }
                    )
    return proposals


class MutualLocationProvider(Protocol):
    def supports(self, location_type: str | None) -> bool: ...

    def provide(self, affiliated: AutonomousSystem, network: Network) -> list[dict]: ...


class PublicLocationProvider:
    """Mutual public peering locations: IXPs shared with the peer network."""

    def supports(self, location_type: str | None) -> bool:
        return location_type in (None, PeeringRequestType.PUBLIC_PEERING)

    def provide(self, affiliated: AutonomousSystem, network: Network) -> list[dict]:
        ixps = [ixp for ixp in affiliated.get_shared_internet_exchange_points(network) if ixp.peeringdb_ixlan_id]
        proposals = session_proposals_by_ixp(ixps, network)
        return [
            {
                "location": format_ix_location(ixp.peeringdb_ixlan_id),
                "name": ixp.name,
                "peering_type": PeeringRequestType.PUBLIC_PEERING,
                "sessions": proposals[ixp.pk],
            }
            for ixp in ixps
        ]


class PrivateLocationProvider:
    """Mutual private peering locations: facilities shared with the peer network."""

    def supports(self, location_type: str | None) -> bool:
        return location_type in (None, PeeringRequestType.PRIVATE_PEERING)

    def provide(self, affiliated: AutonomousSystem, network: Network) -> list[dict]:
        return [
            {
                "location": format_facility_location(fac.pk),
                "name": fac.name,
                "peering_type": PeeringRequestType.PRIVATE_PEERING,
                "sessions": [],
            }
            for fac in affiliated.get_peeringdb_shared_facilities(network)
        ]


class LocationDiscoveryService:
    """Aggregates mutual peering locations from every provider that supports the requested type."""

    def __init__(self, *, providers: Sequence[MutualLocationProvider]) -> None:
        self._providers = providers

    def discover(
        self, *, affiliated: AutonomousSystem, network: Network, location_type: str | None = None
    ) -> list[dict]:
        locations: list[dict] = []
        for provider in self._providers:
            if provider.supports(location_type):
                locations.extend(provider.provide(affiliated, network))
        return locations


def build_location_discovery_service() -> LocationDiscoveryService:
    return LocationDiscoveryService(providers=[PublicLocationProvider(), PrivateLocationProvider()])
