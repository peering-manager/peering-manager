from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from peering_manager.api.exceptions import UnprocessableRequest
from peeringdb.models import NetworkContact

from ...constants import ASN_MAX, ASN_MIN
from ...enums import PeeringRequestType
from ...models import AutonomousSystem
from ...services import (
    PeeringRequestConflictError,
    build_location_discovery_service,
    build_peering_request_service,
)
from ..serializers import (
    PortalAffiliatedSerializer,
    PortalLocationsResponseSerializer,
    PortalNetworkSerializer,
    PortalRequestListSerializer,
    PortalRequestStatusSerializer,
    PortalSessionSubmitResponseSerializer,
    PortalSessionSubmitSerializer,
)
from .portal_helpers import get_network_or_404, get_peering_request_or_404, portal_request_queryset

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from rest_framework.request import Request

NO_AFFILIATED_AS = OpenApiResponse(description="Calling user has no affiliated AS")
ASN_PARAM = OpenApiParameter("asn", OpenApiTypes.INT, OpenApiParameter.QUERY, required=True, description="Peer ASN")
LOCATION_TYPE_PARAM = OpenApiParameter(
    "location_type",
    OpenApiTypes.STR,
    OpenApiParameter.QUERY,
    required=False,
    enum=[PeeringRequestType.PUBLIC_PEERING, PeeringRequestType.PRIVATE_PEERING],
    description="Filter to public or private peering; both when omitted",
)
REQUEST_ID_PARAM = OpenApiParameter(
    "request_id", OpenApiTypes.UUID, OpenApiParameter.QUERY, required=False, description="Filter to one tracking ID"
)


def require_affiliated_as(user: AbstractUser) -> AutonomousSystem:
    affiliated = AutonomousSystem.get_for_user(user=user)
    if affiliated is None:
        raise UnprocessableRequest("User must have an affiliated AS.")
    return affiliated


def require_asn(request: Request) -> int:
    asn = request.query_params.get("asn")
    if not asn:
        raise ValidationError({"asn": "The 'asn' query parameter is required."})
    try:
        value = int(asn)
    except ValueError as exc:
        raise ValidationError({"asn": "The 'asn' query parameter is not a valid integer."}) from exc
    if not ASN_MIN <= value <= ASN_MAX:
        raise ValidationError({"asn": f"The 'asn' query parameter must be between {ASN_MIN} and {ASN_MAX}."})
    return value


class HasPeeringRequestPermission(BasePermission):
    """
    Allows access for users with peering request management permissions.
    """

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and all(request.user.has_perm(p) for p in ("peering.add_peeringrequest", "peering.change_peeringrequest"))
        )


class PortalAPIView(APIView):
    permission_classes = [HasPeeringRequestPermission]


class PortalAffiliatedView(PortalAPIView):
    @extend_schema(
        operation_id="portal_affiliated",
        responses={200: PortalAffiliatedSerializer, 422: NO_AFFILIATED_AS},
    )
    def get(self, request):
        affiliated = require_affiliated_as(user=request.user)
        return Response(PortalAffiliatedSerializer({"asn": affiliated.asn, "name": affiliated.name}).data)


class PortalNetworkView(PortalAPIView):
    @extend_schema(
        operation_id="portal_network_lookup",
        responses={
            200: PortalNetworkSerializer,
            404: OpenApiResponse(description="ASN not found in the PeeringDB cache"),
        },
    )
    def get(self, request, asn: int):
        network = get_network_or_404(asn)
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
        parameters=[ASN_PARAM, LOCATION_TYPE_PARAM],
        responses={
            200: PortalLocationsResponseSerializer,
            404: OpenApiResponse(description="ASN not found in the PeeringDB cache"),
            422: NO_AFFILIATED_AS,
        },
    )
    def get(self, request):
        asn = require_asn(request=request)
        network = get_network_or_404(asn)
        affiliated = require_affiliated_as(user=request.user)

        location_type = request.query_params.get("location_type")
        if location_type is not None and location_type not in (
            PeeringRequestType.PUBLIC_PEERING,
            PeeringRequestType.PRIVATE_PEERING,
        ):
            raise ValidationError({"location_type": f"Unknown location type: {location_type!r}."})

        locations = build_location_discovery_service().discover(
            affiliated=affiliated,
            network=network,
            location_type=location_type,
        )
        return Response(PortalLocationsResponseSerializer({"locations": locations, "peer_asn": affiliated.asn}).data)


class PortalSessionsView(PortalAPIView):
    @extend_schema(
        operation_id="portal_sessions_list",
        parameters=[ASN_PARAM, REQUEST_ID_PARAM],
        responses={200: PortalRequestListSerializer, 422: NO_AFFILIATED_AS},
    )
    def get(self, request):
        asn = require_asn(request=request)
        affiliated = require_affiliated_as(user=request.user)
        qs = portal_request_queryset(affiliated).filter(requesting_asn=asn)

        request_id = request.query_params.get("request_id")
        if request_id:
            try:
                tracking_id = uuid.UUID(request_id)
            except ValueError as exc:
                raise ValidationError({"request_id": "The 'request_id' query parameter is not a valid UUID."}) from exc
            qs = qs.filter(tracking_id=tracking_id)

        return Response(PortalRequestListSerializer({"requests": qs}).data)

    @extend_schema(
        operation_id="portal_sessions_create",
        request=PortalSessionSubmitSerializer,
        responses={
            201: PortalSessionSubmitResponseSerializer,
            400: OpenApiResponse(description="Invalid submission"),
            404: OpenApiResponse(description="ASN not found in the PeeringDB cache"),
            409: OpenApiResponse(
                description="Sessions conflict with pending or existing ones; `code` is `duplicate_pending` "
                "or `already_configured` and `conflicting_ips` lists the culprits"
            ),
            422: NO_AFFILIATED_AS,
        },
    )
    def post(self, request):
        serializer = PortalSessionSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        get_network_or_404(data["local_asn"])
        affiliated = require_affiliated_as(user=request.user)

        try:
            pr = build_peering_request_service().submit(
                local_autonomous_system=affiliated,
                requesting_asn=data["local_asn"],
                request_type=data["peer_type"],
                sessions=data["sessions"],
                requester_email=data["email"],
            )
        except PeeringRequestConflictError as e:
            return Response(
                {"detail": e.detail, "code": e.code, "conflicting_ips": e.ips}, status=status.HTTP_409_CONFLICT
            )
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict) from e

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
        responses={
            200: PortalRequestStatusSerializer,
            404: OpenApiResponse(description="Unknown tracking ID"),
            422: NO_AFFILIATED_AS,
        },
    )
    def get(self, request, request_id: str):
        affiliated = require_affiliated_as(user=request.user)
        pr = get_peering_request_or_404(affiliated, request_id)
        return Response(PortalRequestStatusSerializer(pr).data)

    @extend_schema(
        operation_id="portal_sessions_cancel",
        responses={
            204: OpenApiResponse(description="Request cancelled"),
            404: OpenApiResponse(description="Unknown tracking ID"),
            409: OpenApiResponse(description="Cannot cancel"),
            422: NO_AFFILIATED_AS,
        },
    )
    def delete(self, request, request_id: str):
        affiliated = require_affiliated_as(user=request.user)
        pr = get_peering_request_or_404(affiliated, request_id)

        try:
            pr.cancel()
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)

        return Response(status=status.HTTP_204_NO_CONTENT)


