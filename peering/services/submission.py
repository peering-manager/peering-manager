from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from net.models import Connection
from peeringdb.models import Facility, IXLan

from ..constants import FACILITY_LOCATION_PREFIX, IX_LOCATION_PREFIX
from ..enums import PeeringRequestStatus, PeeringRequestType
from ..functions import ip_host
from ..models import (
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    PeeringRequest,
    RequestedSession,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from ..models import AutonomousSystem

__all__ = (
    "DuplicatePendingRequestError",
    "PeeringRequestConflictError",
    "PeeringRequestService",
    "PrivateSessionResolver",
    "PublicSessionResolver",
    "ResolvedSession",
    "SessionConflictChecker",
    "SessionResolver",
    "SessionsAlreadyConfiguredError",
    "build_peering_request_service",
)


@dataclass(frozen=True)
class ResolvedSession:
    """A submitted session with its location resolved to database records."""

    local_ip: str
    peer_ip: str = ""
    session_secret: str = ""
    facility: Facility | None = None
    connection: Connection | None = None


class PeeringRequestConflictError(Exception):
    """A submitted session collides with a pending request or an existing session."""

    code = "conflict"

    def __init__(self, detail: str, ips: Iterable[str]) -> None:
        super().__init__(detail)
        self.detail = detail
        self.ips = sorted(set(ips))


class DuplicatePendingRequestError(PeeringRequestConflictError):
    """Sessions with the same IPs are already pending for this ASN."""

    code = "duplicate_pending"


class SessionsAlreadyConfiguredError(PeeringRequestConflictError):
    """Sessions with the same IPs already exist as real BGP sessions."""

    code = "already_configured"


class SessionResolver(Protocol):
    def supports(self, peer_type: str) -> bool: ...

    def resolve(self, session: Mapping) -> ResolvedSession: ...


class PublicSessionResolver:
    """Resolves a public-peering session against an IXP LAN and a peer connection."""

    def supports(self, peer_type: str) -> bool:
        return peer_type == PeeringRequestType.PUBLIC_PEERING

    def resolve(self, session: Mapping) -> ResolvedSession:
        ix = self._resolve_ix(session.get("location", ""))
        connection = self._resolve_peer_connection(ix, session.get("peer_ip", ""))
        return ResolvedSession(
            local_ip=session["local_ip"],
            peer_ip=session.get("peer_ip", ""),
            session_secret=session.get("session_secret", ""),
            connection=connection,
        )

    def _resolve_ix(self, location: str) -> InternetExchange:
        if not location.startswith(IX_LOCATION_PREFIX):
            raise ValidationError({"location": f"Public peering location must use '{IX_LOCATION_PREFIX}<id>' format."})
        try:
            ixlan = IXLan.objects.get(pk=int(location.removeprefix(IX_LOCATION_PREFIX)))
        except (ValueError, IXLan.DoesNotExist) as exc:
            raise ValidationError({"location": f"Unknown IX: {location!r}."}) from exc
        ix = InternetExchange.objects.filter(peeringdb_ixlan=ixlan).first()
        if ix is None:
            raise ValidationError({"location": f"IX {location!r} not found."})
        return ix

    def _resolve_peer_connection(self, ixp: InternetExchange, peer_ip: str) -> Connection:
        """Match on host address only, prefix length differences are tolerated."""
        if not peer_ip:
            raise ValidationError({"peer_ip": "Required for public peering."})
        try:
            host = str(ip_host(peer_ip))
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


class PrivateSessionResolver:
    """Resolves a private-peering session against a facility."""

    def supports(self, peer_type: str) -> bool:
        return peer_type == PeeringRequestType.PRIVATE_PEERING

    def resolve(self, session: Mapping) -> ResolvedSession:
        facility = self._resolve_facility(session.get("location", ""))
        if not session.get("peer_ip"):
            raise ValidationError({"peer_ip": "Required for private peering."})
        # The prefix length is needed to configure the interconnect interfaces on both routers
        for field in ("local_ip", "peer_ip"):
            if "/" not in session[field]:
                raise ValidationError({field: "A prefix length is required for private peering, e.g. 192.0.2.1/30."})
        return ResolvedSession(
            local_ip=session["local_ip"],
            peer_ip=session["peer_ip"],
            session_secret=session.get("session_secret", ""),
            facility=facility,
        )

    def _resolve_facility(self, location: str) -> Facility:
        if not location.startswith(FACILITY_LOCATION_PREFIX):
            raise ValidationError(
                {"location": f"Private peering location must use '{FACILITY_LOCATION_PREFIX}<id>' format."}
            )
        try:
            return Facility.objects.get(pk=int(location.removeprefix(FACILITY_LOCATION_PREFIX)))
        except (ValueError, Facility.DoesNotExist) as exc:
            raise ValidationError({"location": f"Unknown facility: {location!r}."}) from exc


class SessionConflictChecker:
    """Rejects sessions already pending for the ASN or already configured as real BGP sessions."""

    def check(self, requesting_asn: int, resolved: Sequence[ResolvedSession]) -> None:
        # Host addresses are compared as notations can differ (prefix length, IPv6 case)
        pending_hosts = {
            str(ip_host(ip))
            for ip in RequestedSession.objects.filter(
                peering_request__requesting_asn=requesting_asn,
                peering_request__status=PeeringRequestStatus.PENDING,
            ).values_list("ip_address", flat=True)
        }
        submitted_hosts = {str(ip_host(s.local_ip)) for s in resolved}
        overlap = submitted_hosts & pending_hosts
        if overlap:
            raise DuplicatePendingRequestError(
                "Duplicate request: sessions with these IPs are already pending.", overlap
            )

        conflicting: list[str] = []
        for s in resolved:
            if s.connection is not None:
                # `InternetExchangePeeringSession.ip_address` stores no prefix, so the field normalizes the
                # submitted value to host form and this exact match stays notation-insensitive
                exists = InternetExchangePeeringSession.exists_at(s.connection, s.local_ip)
            else:
                # `DirectPeeringSession.ip_address` stores a prefix length, match on host address only
                exists = DirectPeeringSession.objects.filter(
                    autonomous_system__asn=requesting_asn, ip_address__host=str(ip_host(s.local_ip))
                ).exists()
            if exists:
                conflicting.append(str(ip_host(s.local_ip)))
        if conflicting:
            raise SessionsAlreadyConfiguredError("Sessions with these IPs are already configured.", conflicting)


class PeeringRequestService:
    """Validates a portal submission and atomically creates a `PeeringRequest` with its `RequestedSession`s."""

    def __init__(
        self,
        *,
        session_resolvers: Sequence[SessionResolver],
        conflict_checker: SessionConflictChecker,
    ) -> None:
        self._session_resolvers = session_resolvers
        self._conflict_checker = conflict_checker

    @transaction.atomic
    def submit(
        self,
        *,
        local_autonomous_system: AutonomousSystem,
        requesting_asn: int,
        request_type: str,
        sessions: Sequence[Mapping],
        requester_email: str = "",
    ) -> PeeringRequest:
        """
        `sessions` is a sequence of mappings with `local_ip`, `location` and optional `peer_ip`/`session_secret`
        keys. Raises `django.core.exceptions.ValidationError` on invalid input and a `PeeringRequestConflictError`
        subclass when sessions collide with pending or existing ones.
        """
        resolver = self._resolver_for(request_type)
        self._reject_duplicate_sessions(sessions)
        resolved = [resolver.resolve(s) for s in sessions]
        # Check-then-create without locking: two simultaneous submissions of the same IPs can both pass;
        # duplicates are still caught at review time, so the race is accepted
        self._conflict_checker.check(requesting_asn, resolved)

        pr = PeeringRequest.objects.create(
            requesting_asn=requesting_asn,
            requester_email=requester_email,
            local_autonomous_system=local_autonomous_system,
            request_type=request_type,
        )
        for s in resolved:
            RequestedSession.objects.create(
                peering_request=pr,
                ixp_connection=s.connection,
                peeringdb_facility=s.facility,
                ip_address=s.local_ip,
                peer_ip_address=s.peer_ip or None,
                session_secret=s.session_secret,
            )
        return pr

    def _resolver_for(self, peer_type: str) -> SessionResolver:
        for resolver in self._session_resolvers:
            if resolver.supports(peer_type):
                return resolver
        raise ValidationError({"peer_type": f"Unsupported peering type: {peer_type!r}."})

    @staticmethod
    def _reject_duplicate_sessions(sessions: Sequence[Mapping]) -> None:
        """The same IP can still be requested at several locations or peer connections at once."""
        seen: set[tuple[str, str, str]] = set()
        duplicated: set[str] = set()
        for s in sessions:
            host = str(ip_host(s["local_ip"]))
            key = (s.get("location", ""), host, str(ip_host(s["peer_ip"])) if s.get("peer_ip") else "")
            if key in seen:
                duplicated.add(host)
            seen.add(key)
        if duplicated:
            raise ValidationError(
                {"sessions": f"Duplicate sessions in submission for IPs: {', '.join(sorted(duplicated))}."}
            )


def build_peering_request_service() -> PeeringRequestService:
    return PeeringRequestService(
        session_resolvers=[PublicSessionResolver(), PrivateSessionResolver()],
        conflict_checker=SessionConflictChecker(),
    )
