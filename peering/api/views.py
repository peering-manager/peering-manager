from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import APIRootView

from core.api.serializers import JobSerializer
from core.models import Job
from devices.jobs import poll_bgp_sessions
from messaging.api.serializers import EmailSendingSerializer
from messaging.models import Email
from peering_manager.api.exceptions import ServiceUnavailable
from peering_manager.api.viewsets import PeeringManagerModelViewSet
from peeringdb.api.serializers import FacilitySerializer, NetworkIXLanSerializer

from ..filtersets import (
    AutonomousSystemFilterSet,
    BGPGroupFilterSet,
    DirectPeeringSessionFilterSet,
    InternetExchangeFilterSet,
    InternetExchangePeeringSessionFilterSet,
    RoutingPolicyFilterSet,
)
from ..jobs import import_sessions_to_internet_exchange
from ..models import (
    AutonomousSystem,
    BGPGroup,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)
from .serializers import (
    AutonomousSystemSerializer,
    BGPGroupSerializer,
    DirectPeeringSessionSerializer,
    InternetExchangePeeringSessionSerializer,
    InternetExchangeSerializer,
    NestedInternetExchangeSerializer,
    RoutingPolicySerializer,
)


class PeeringRootView(APIRootView):
    def get_view_name(self):
        return "Peering"


class AutonomousSystemViewSet(PeeringManagerModelViewSet):
    queryset = AutonomousSystem.objects.all()
    serializer_class = AutonomousSystemSerializer
    filterset_class = AutonomousSystemFilterSet

    @extend_schema(
        operation_id="peering_autonomous_systems_poll_bgp_sessions",
        responses={
            202: OpenApiResponse(
                response=JobSerializer(many=True),
                description="Jobs scheduled to poll BGP sessions.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to poll BGP sessions state.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The autonomous system does not exist.",
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="poll-bgp-sessions")
    def poll_bgp_sessions(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm(
            "peering.change_directpeeringsession"
        ) or not request.user.has_perm("peering.change_internetexchangepeeringsession"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        jobs = []
        for router in self.get_object().get_routers():
            jobs.append(
                Job.enqueue(
                    poll_bgp_sessions,
                    router,
                    name="devices.router.poll_bgp_sessions",
                    object=router,
                    user=request.user,
                )
            )
        return Response(
            JobSerializer(jobs, many=True, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="peering_autonomous_systems_sync_with_peeringdb",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The synchronisation has been done.",
            ),
            204: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The synchronisation cannot be done.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission update the AS.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The AS does not exist."
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="sync-with-peeringdb")
    def sync_with_peeringdb(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.change_autonomoussystem"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        success = self.get_object().synchronise_with_peeringdb()
        return Response(
            status=status.HTTP_200_OK if success else status.HTTP_204_NO_CONTENT
        )

    @extend_schema(
        operation_id="peering_autonomous_systems_as_set_prefixes",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Retrieves the prefix list for the AS.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The AS does not exist."
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="as-set-prefixes")
    def as_set_prefixes(self, request, pk=None):
        return Response(data=self.get_object().get_irr_as_set_prefixes())

    @extend_schema(
        operation_id="peering_autonomous_systems_shared_ixps",
        responses={
            200: OpenApiResponse(
                response=NestedInternetExchangeSerializer(many=True),
                description="Retrieves the shared IXPs with the AS.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The AS does not exist."
            ),
            503: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The user has no affiliated AS.",
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="shared-ixps")
    def shared_ixps(self, request, pk=None):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
        except AutonomousSystem.DoesNotExist:
            raise ServiceUnavailable("User did not choose an affiliated AS.") from None

        return Response(
            data=NestedInternetExchangeSerializer(
                self.get_object().get_shared_internet_exchange_points(affiliated),
                many=True,
                context={"request": request},
            ).data
        )

    @extend_schema(
        operation_id="peering_autonomous_systems_shared_facilities",
        responses={
            200: OpenApiResponse(
                response=NestedInternetExchangeSerializer(many=True),
                description="Retrieves the shared facilities with the AS.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The AS does not exist."
            ),
            503: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The user has no affiliated AS.",
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="shared-facilities")
    def shared_facilities(self, request, pk=None):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
        except AutonomousSystem.DoesNotExist:
            raise ServiceUnavailable("User did not choose an affiliated AS.") from None

        return Response(
            data=FacilitySerializer(
                self.get_object().get_peeringdb_shared_facilities(affiliated),
                many=True,
                context={"request": request},
            ).data
        )

    # TODO: Rename from generate to render in URL in next release
    @extend_schema(
        operation_id="peering_autonomous_systems_render_email",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="Renders the e-mail template."
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The AS or e-mail template does not exist.",
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="generate-email")
    def generate_email(self, request, pk=None):
        # Make sure request is valid
        serializer = EmailSendingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            template = Email.objects.get(pk=serializer.validated_data.get("email"))
            rendered = self.get_object().render_email(template)
            return Response(data={"subject": rendered[0], "body": rendered[1]})
        except Email.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class BGPGroupViewSet(PeeringManagerModelViewSet):
    queryset = BGPGroup.objects.all()
    serializer_class = BGPGroupSerializer
    filterset_class = BGPGroupFilterSet

    @extend_schema(
        operation_id="peering_bgp_groups_poll_bgp_sessions",
        responses={
            202: OpenApiResponse(
                response=JobSerializer(many=True),
                description="Jobs scheduled to poll BGP sessions.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to poll BGP sessions state.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The BGP group does not exist.",
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="poll-bgp-sessions")
    def poll_bgp_sessions(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.change_directpeeringsession"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        jobs = []
        for router in self.get_object().get_routers():
            jobs.append(
                Job.enqueue(
                    poll_bgp_sessions,
                    router,
                    name="devices.router.poll_bgp_sessions",
                    object=router,
                    user=request.user,
                )
            )
        return Response(
            JobSerializer(jobs, many=True, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )


class DirectPeeringSessionViewSet(PeeringManagerModelViewSet):
    queryset = DirectPeeringSession.objects.all()
    serializer_class = DirectPeeringSessionSerializer
    filterset_class = DirectPeeringSessionFilterSet

    @extend_schema(
        operation_id="peering_direct_peering_sessions_encrypt_password",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The session password has been encrypted.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to encrypt the password.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The direct peering session does not exist.",
            ),
            503: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The session has not been encrypted.",
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="encrypt-password")
    def encrypt_password(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.change_directpeeringsession"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        success = self.get_object().encrypt_password(commit=True)
        return Response(
            status=(
                status.HTTP_200_OK if success else status.HTTP_503_SERVICE_UNAVAILABLE
            )
        )

    @extend_schema(
        operation_id="peering_direct_peering_sessions_poll",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The session status has been polled.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to poll session status.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The direct peering session does not exist.",
            ),
            503: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The session status has not been polled.",
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="poll")
    def poll(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.change_directpeeringsession"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        success = self.get_object().poll()
        return Response(
            status=(
                status.HTTP_200_OK if success else status.HTTP_503_SERVICE_UNAVAILABLE
            )
        )


class InternetExchangeViewSet(PeeringManagerModelViewSet):
    queryset = InternetExchange.objects.all()
    serializer_class = InternetExchangeSerializer
    filterset_class = InternetExchangeFilterSet

    @extend_schema(
        operation_id="peering_internet_exchange_link_to_peeringdb",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The IXP is linked with a PeeringDB record.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to update the IXP.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The IXP does not exist."
            ),
            503: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The IXP is not linked with a PeeringDB record.",
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="link-to-peeringdb")
    def link_to_peeringdb(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.change_internetexchange"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        ixlan = self.get_object().link_to_peeringdb()
        return Response(
            status=(
                status.HTTP_200_OK
                if ixlan is not None
                else status.HTTP_503_SERVICE_UNAVAILABLE
            )
        )

    @extend_schema(
        operation_id="peering_internet_exchange_available_peers",
        responses={
            200: OpenApiResponse(
                response=NetworkIXLanSerializer(many=True),
                description="The PeeringDB records of available peers.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The IXP does not exist."
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="available-peers")
    def available_peers(self, request, pk=None):
        return Response(
            data=NetworkIXLanSerializer(
                self.get_object().get_available_peers(),
                many=True,
                context={"request": request},
            ).data
        )

    @extend_schema(
        operation_id="peering_internet_exchanges_import_sessions",
        responses={
            202: OpenApiResponse(
                response=JobSerializer,
                description="Session import job is scheduled.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to update the IXP sessions.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The IXP does not exist."
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="import-sessions")
    def import_sessions(self, request, pk=None):
        if not request.user.has_perm("peering.add_internetexchangepeeringsession"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        ixp = self.get_object()
        job = Job.enqueue(
            import_sessions_to_internet_exchange,
            ixp,
            name="peering.internet_exchange.import_sessions",
            object=ixp,
            user=request.user,
        )
        return Response(
            data=JobSerializer(instance=job, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    # DEPRECATED
    # TODO: remove in next feature release
    @extend_schema(
        operation_id="peering_internet_exchanges_prefixes",
        request=None,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The prefixes attached to the IXP sorted by address family.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The IXP does not exist."
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="prefixes")
    def prefixes(self, request, pk=None):
        prefixes = {}
        for p in self.get_object().get_prefixes():
            if p.prefix.version == 6:
                ipv6 = prefixes.setdefault("ipv6", [])
                ipv6.append(str(p.prefix))
            if p.prefix.version == 4:
                ipv4 = prefixes.setdefault("ipv4", [])
                ipv4.append(str(p.prefix))

        return Response(data=prefixes)

    @extend_schema(
        operation_id="peering_internet_exchanges_poll_bgp_sessions",
        responses={
            202: OpenApiResponse(
                response=JobSerializer(many=True),
                description="Jobs scheduled to poll BGP sessions.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to poll BGP sessions state.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The IXP does not exist.",
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="poll-bgp-sessions")
    def poll_bgp_sessions(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.change_internetexchangepeeringsession"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        jobs = []
        for router in self.get_object().get_routers():
            jobs.append(
                Job.enqueue(
                    poll_bgp_sessions,
                    router,
                    name="devices.router.poll_bgp_sessions",
                    object=router,
                    user=request.user,
                )
            )
        return Response(
            JobSerializer(jobs, many=True, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )


class InternetExchangePeeringSessionViewSet(PeeringManagerModelViewSet):
    queryset = InternetExchangePeeringSession.objects.all()
    serializer_class = InternetExchangePeeringSessionSerializer
    filterset_class = InternetExchangePeeringSessionFilterSet

    @extend_schema(
        operation_id="peering_internet_exchange_peering_sessions_encrypt_password",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The session password has been encrypted.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to encrypt the password.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The Internet exchange peering session does not exist.",
            ),
            503: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The session has not been encrypted.",
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="encrypt-password")
    def encrypt_password(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.change_internetexchangepeeringsession"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        success = self.get_object().encrypt_password(commit=True)
        return Response(
            status=(
                status.HTTP_200_OK if success else status.HTTP_503_SERVICE_UNAVAILABLE
            )
        )

    @extend_schema(
        operation_id="peering_internet_exchange_peering_sessions_poll",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The session status has been polled.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to poll session status.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The Internet exchange peering session does not exist.",
            ),
            503: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The session status has not been polled.",
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="poll")
    def poll(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.change_internetexchangepeeringsession"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        success = self.get_object().poll()
        return Response(
            status=(
                status.HTTP_200_OK if success else status.HTTP_503_SERVICE_UNAVAILABLE
            )
        )


class RoutingPolicyViewSet(PeeringManagerModelViewSet):
    queryset = RoutingPolicy.objects.all()
    serializer_class = RoutingPolicySerializer
    filterset_class = RoutingPolicyFilterSet
