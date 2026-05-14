from __future__ import annotations

from typing import TYPE_CHECKING

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from peering_manager.api.exceptions import ServiceUnavailable
from peeringdb.models import Network, NetworkContact

from ...enums import PeeringRequestStatus, PeeringRequestType
from ...models import (
    AutonomousSystem,
    DirectPeeringSession,
    InternetExchangePeeringSession,
    PeeringRequest,
    RequestedSession,
)
from ..constants import IX_LOCATION_PREFIX
from ..serializers import (
    PortalNetworkSerializer,
    PortalRequestStatusSerializer,
    PortalSessionSubmitResponseSerializer,
    PortalSessionSubmitSerializer,
)
from .portal_helpers import resolve_location, resolve_peer_connection, session_proposals

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from rest_framework.request import Request


def require_affiliated_as(user: AbstractUser) -> AutonomousSystem:
    affiliated = AutonomousSystem.get_for_user(user=user)
    if affiliated is None:
        raise ServiceUnavailable("User must have an affiliated AS.")
    return affiliated


def require_asn(request: Request) -> int:
    asn = request.query_params.get("asn")
    if not asn:
        raise ValidationError({"asn": "The 'asn' query parameter is required."})
    try:
        return int(asn)
    except ValueError as exc:
        raise ValidationError(
            {"asn": "The 'asn' query parameter is not a valid integer."}
        ) from exc


class HasPeeringRequestPermission(BasePermission):
    """
    Allows access for users with peering request management permissions.
    """

    def has_permission(self, request, view) -> bool:
        return request.user and all(
            request.user.has_perm(p)
            for p in ("peering.add_peering_request", "peering.change_peering_request")
        )


class PortalAPIView(APIView):
    permission_classes = [HasPeeringRequestPermission]


class PortalAffiliatedView(PortalAPIView):
    @extend_schema(
        operation_id="portal_affiliated",
        responses={
            200: OpenApiResponse(description="Affiliated AS for the calling token"),
            503: OpenApiResponse(description="Calling user has no affiliated AS"),
        },
    )
    def get(self, request):
        affiliated = require_affiliated_as(user=request.user)
        return Response({"asn": affiliated.asn, "name": affiliated.name})


class PortalNetworkView(PortalAPIView):
    @extend_schema(
        operation_id="portal_network_lookup",
        responses={200: OpenApiResponse(description="Network details from PeeringDB")},
    )
    def get(self, request, asn: int):
        try:
            network = Network.objects.get(asn=asn)
        except Network.DoesNotExist:
            return Response(
                {"detail": f"ASN {asn} not found in PeeringDB cache."},
                status=status.HTTP_404_NOT_FOUND,
            )

        contacts = [
            {"name": c.name, "email": c.email, "role": c.role}
            for c in NetworkContact.objects.filter(net=network).exclude(email="")
        ]

        data = PortalNetworkSerializer(
            {
                "asn": network.asn,
                "name": network.name,
                "name_long": network.name_long,
                "info_prefixes4": network.info_prefixes4,
                "info_prefixes6": network.info_prefixes6,
                "irr_as_set": network.irr_as_set,
                "policy_general": network.policy_general,
                "contacts": contacts,
            }
        ).data
        return Response(data)


class PortalLocationView(PortalAPIView):
    @extend_schema(
        operation_id="portal_locations_list",
        responses={200: OpenApiResponse(description="Mutual peering locations")},
    )
    def get(self, request):
        asn = require_asn(request=request)
        try:
            network = Network.objects.get(asn=asn)
        except Network.DoesNotExist:
            return Response(
                {"detail": f"ASN {asn} not found in PeeringDB cache."},
                status=status.HTTP_404_NOT_FOUND,
            )

        affiliated = require_affiliated_as(user=request.user)
        location_type = request.query_params.get("location_type")
        locations: list[dict] = []

        if location_type in (None, PeeringRequestType.PUBLIC_PEERING):
            for ixp in affiliated.get_shared_internet_exchange_points(network):
                if not ixp.peeringdb_ixlan:
                    continue
                locations.append(
                    {
                        "location": f"{IX_LOCATION_PREFIX}{ixp.peeringdb_ixlan.pk}",
                        "name": ixp.name,
                        "peering_type": PeeringRequestType.PUBLIC_PEERING,
                        "sessions": session_proposals(ixp, network),
                    }
                )

        if location_type in (None, PeeringRequestType.PRIVATE_PEERING):
            shared_facilities = affiliated.get_peeringdb_shared_facilities(network)
            for fac in shared_facilities:
                locations.append(
                    {
                        "location": str(fac.pk),
                        "name": fac.name,
                        "peering_type": PeeringRequestType.PRIVATE_PEERING,
                        "sessions": [],
                    }
                )

        return Response({"locations": locations, "peer_asn": affiliated.asn})


class PortalSessionCreateView(PortalAPIView):
    @extend_schema(
        operation_id="portal_sessions_create",
        request=None,
        responses={201: OpenApiResponse(description="Peering request created")},
    )
    def post(self, request):
        serializer = PortalSessionSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            Network.objects.get(asn=data["local_asn"])
        except Network.DoesNotExist:
            return Response(
                {"detail": f"ASN {data['local_asn']} not found in PeeringDB cache."},
                status=status.HTTP_404_NOT_FOUND,
            )

        affiliated = require_affiliated_as(user=request.user)

        # Resolve location + peer IP per session before writing anything
        resolved: list[tuple[dict, object, object]] = []
        for s in data["sessions"]:
            ix, facility = resolve_location(data["peer_type"], s.get("location", ""))
            connection = None
            if ix is not None:
                connection = resolve_peer_connection(ix, s.get("peer_ip", ""))
            resolved.append((s, facility, connection))

        # Reject IPs already covered by a pending request from the same ASN
        pending_ips = set(
            RequestedSession.objects.filter(
                peering_request__requesting_asn=data["local_asn"],
                peering_request__status=PeeringRequestStatus.PENDING,
            ).values_list("ip_address", flat=True)
        )
        submitted_ips = {s["local_ip"] for s in data["sessions"]}
        overlap = submitted_ips & {str(ip) for ip in pending_ips}
        if overlap:
            return Response(
                {
                    "detail": "Duplicate request: sessions with these IPs are already pending.",
                    "overlapping_ips": sorted(overlap),
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Reject sessions already configured as real BGP sessions
        conflicting: list[str] = []
        for session_data, _facility, connection in resolved:
            ip = session_data["local_ip"]
            if connection is not None:
                exists = InternetExchangePeeringSession.exists_at(connection, ip)
            else:
                exists = DirectPeeringSession.objects.filter(
                    autonomous_system__asn=data["local_asn"], ip_address=ip
                ).exists()

            if exists:
                conflicting.append(ip)

        if conflicting:
            return Response(
                {
                    "detail": "Sessions with these IPs are already configured.",
                    "existing_session_ips": sorted(set(conflicting)),
                },
                status=status.HTTP_409_CONFLICT,
            )

        pr = PeeringRequest.create_with_sessions(
            local_autonomous_system=affiliated,
            requesting_asn=data["local_asn"],
            request_type=data["peer_type"],
            sessions=resolved,
            requester_email=data.get("email", ""),
        )

        response_data = PortalSessionSubmitResponseSerializer(
            {
                "request_id": pr.tracking_id,
                "status": pr.status,
                "sessions_count": pr.requested_sessions.count(),
            }
        ).data
        return Response(response_data, status=status.HTTP_201_CREATED)


class PortalSessionDetailView(PortalAPIView):
    @extend_schema(
        operation_id="portal_sessions_retrieve",
        responses={200: OpenApiResponse(description="Peering request status")},
    )
    def get(self, request, request_id: str):
        affiliated = require_affiliated_as(user=request.user)
        try:
            pr = (
                PeeringRequest.objects.select_related("local_autonomous_system")
                .prefetch_related(
                    "requested_sessions__ixp_connection__internet_exchange_point__peeringdb_ixlan",
                    "requested_sessions__peeringdb_facility",
                )
                .get(tracking_id=request_id, local_autonomous_system=affiliated)
            )
        except (PeeringRequest.DoesNotExist, ValueError):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(PortalRequestStatusSerializer(pr).data)

    @extend_schema(
        operation_id="portal_sessions_cancel",
        responses={
            204: OpenApiResponse(description="Request cancelled"),
            409: OpenApiResponse(description="Cannot cancel"),
        },
    )
    def delete(self, request, request_id: str):
        affiliated = require_affiliated_as(user=request.user)
        try:
            pr = PeeringRequest.objects.get(
                tracking_id=request_id, local_autonomous_system=affiliated
            )
        except (PeeringRequest.DoesNotExist, ValueError):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            pr.cancel()
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)

        return Response(status=status.HTTP_204_NO_CONTENT)


class PortalSessionListView(PortalAPIView):
    @extend_schema(
        operation_id="portal_sessions_list",
        responses={200: OpenApiResponse(description="List of peering requests")},
    )
    def get(self, request):
        asn = require_asn(request=request)
        affiliated = require_affiliated_as(user=request.user)
        qs = (
            PeeringRequest.objects.select_related("local_autonomous_system")
            .prefetch_related(
                "requested_sessions__ixp_connection__internet_exchange_point__peeringdb_ixlan",
                "requested_sessions__peeringdb_facility",
            )
            .filter(local_autonomous_system=affiliated, requesting_asn=int(asn))
        )

        request_id = request.query_params.get("request_id")
        if request_id:
            qs = qs.filter(tracking_id=request_id)

        return Response({"requests": PortalRequestStatusSerializer(qs, many=True).data})
