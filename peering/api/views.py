from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.routers import APIRootView

from extras.api.serializers import JobResultSerializer
from extras.models import JobResult
from messaging.models import Email
from peering.filters import (
    AutonomousSystemFilterSet,
    BGPGroupFilterSet,
    CommunityFilterSet,
    ConfigurationFilterSet,
    DirectPeeringSessionFilterSet,
    InternetExchangeFilterSet,
    InternetExchangePeeringSessionFilterSet,
    RouterFilterSet,
    RoutingPolicyFilterSet,
)
from peering.jobs import (
    generate_configuration,
    import_sessions_to_internet_exchange,
    poll_peering_sessions,
    set_napalm_configuration,
    test_napalm_connection,
)
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    Configuration,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from peering_manager.api.exceptions import ServiceUnavailable
from peering_manager.api.views import ModelViewSet
from peeringdb.api.serializers import NetworkIXLanSerializer

from .serializers import (
    AutonomousSystemGenerateEmailSerializer,
    AutonomousSystemSerializer,
    BGPGroupSerializer,
    CommunitySerializer,
    ConfigurationSerializer,
    DirectPeeringSessionSerializer,
    InternetExchangePeeringSessionSerializer,
    InternetExchangeSerializer,
    NestedInternetExchangeSerializer,
    RouterConfigureSerializer,
    RouterSerializer,
    RoutingPolicySerializer,
)


class PeeringRootView(APIRootView):
    def get_view_name(self):
        return "Peering"


class AutonomousSystemViewSet(ModelViewSet):
    queryset = AutonomousSystem.objects.defer("prefixes")
    serializer_class = AutonomousSystemSerializer
    filterset_class = AutonomousSystemFilterSet

    @extend_schema(
        operation_id="peering_autonomous_systems_sync_with_peeringdb",
        request=None,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The synchronization has been done.",
            ),
            204: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The synchronization cannot be done.",
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

        success = self.get_object().synchronize_with_peeringdb()
        return Response(
            status=status.HTTP_200_OK if success else status.HTTP_204_NO_CONTENT
        )

    @extend_schema(
        operation_id="peering_autonomous_systems_as_set_prefixes",
        request=None,
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
        request=None,
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
            raise ServiceUnavailable("User did not choose an affiliated AS.")

        return Response(
            data=NestedInternetExchangeSerializer(
                self.get_object().get_shared_internet_exchange_points(affiliated),
                many=True,
                context={"request": request},
            ).data
        )

    @extend_schema(
        operation_id="peering_autonomous_systems_generate_email",
        request=None,
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
        serializer = AutonomousSystemGenerateEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            template = Email.objects.get(pk=serializer.validated_data.get("email"))
            rendered = self.get_object().generate_email(template)
            return Response(data={"subject": rendered[0], "body": rendered[1]})
        except Email.DoesNotExist:
            raise Response(status=status.HTTP_404_NOT_FOUND)


class BGPGroupViewSet(ModelViewSet):
    queryset = BGPGroup.objects.all()
    serializer_class = BGPGroupSerializer
    filterset_class = BGPGroupFilterSet

    @extend_schema(
        operation_id="peering_bgp_groups_poll_sessions",
        request=None,
        responses={
            202: OpenApiResponse(
                response=JobResultSerializer,
                description="Job scheduled to poll sessions.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to poll session status.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The BGP group does not exist.",
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="poll-sessions")
    def poll_sessions(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.change_directpeeringsession"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        job_result = JobResult.enqueue_job(
            poll_peering_sessions,
            "peering.bgpgroup.poll_peering_sessions",
            BGPGroup,
            request.user,
            self.get_object(),
        )
        return Response(
            data=JobResultSerializer(
                instance=job_result, context={"request": request}
            ).data,
            status=status.HTTP_202_ACCEPTED,
        )


class CommunityViewSet(ModelViewSet):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    filterset_class = CommunityFilterSet


class ConfigurationViewSet(ModelViewSet):
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer
    filterset_class = ConfigurationFilterSet


class DirectPeeringSessionViewSet(ModelViewSet):
    queryset = DirectPeeringSession.objects.all()
    serializer_class = DirectPeeringSessionSerializer
    filterset_class = DirectPeeringSessionFilterSet

    @extend_schema(
        operation_id="peering_direct_peering_sessions_encrypt_password",
        request=None,
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
            status=status.HTTP_200_OK
            if success
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )

    @extend_schema(
        operation_id="peering_direct_peering_sessions_poll",
        request=None,
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
            status=status.HTTP_200_OK
            if success
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )


class InternetExchangeViewSet(ModelViewSet):
    queryset = InternetExchange.objects.all()
    serializer_class = InternetExchangeSerializer
    filterset_class = InternetExchangeFilterSet

    @extend_schema(
        operation_id="peering_internet_exchange_link_to_peeringdb",
        request=None,
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
            status=status.HTTP_200_OK
            if ixlan is not None
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )

    @extend_schema(
        operation_id="peering_internet_exchange_available_peers",
        request=None,
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
        request=None,
        responses={
            202: OpenApiResponse(
                response=JobResultSerializer,
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

        job_result = JobResult.enqueue_job(
            import_sessions_to_internet_exchange,
            "peering.internet_exchange.import_sessions",
            InternetExchange,
            request.user,
            self.get_object(),
        )
        return Response(
            data=JobResultSerializer(
                instance=job_result, context={"request": request}
            ).data,
            status=status.HTTP_202_ACCEPTED,
        )

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
        operation_id="peering_internet_exchanges_poll_sessions",
        request=None,
        responses={
            202: OpenApiResponse(
                response=JobResultSerializer,
                description="Job scheduled to poll sessions.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to poll session status.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The IXP does not exist."
            ),
        },
    )
    @action(detail=True, methods=["post"], url_path="poll-sessions")
    def poll_sessions(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.change_internetexchangepeeringsession"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        job_result = JobResult.enqueue_job(
            poll_peering_sessions,
            "peering.internetexchange.poll_peering_sessions",
            InternetExchange,
            request.user,
            self.get_object(),
        )
        return Response(
            data=JobResultSerializer(
                instance=job_result, context={"request": request}
            ).data,
            status=status.HTTP_202_ACCEPTED,
        )


class InternetExchangePeeringSessionViewSet(ModelViewSet):
    queryset = InternetExchangePeeringSession.objects.all()
    serializer_class = InternetExchangePeeringSessionSerializer
    filterset_class = InternetExchangePeeringSessionFilterSet

    @extend_schema(
        operation_id="peering_internet_exchange_peering_sessions_encrypt_password",
        request=None,
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
            status=status.HTTP_200_OK
            if success
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )

    @extend_schema(
        operation_id="peering_internet_exchange_peering_sessions_poll",
        request=None,
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
            status=status.HTTP_200_OK
            if success
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )


class RouterViewSet(ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    filterset_class = RouterFilterSet

    @extend_schema(
        operation_id="peering_routers_configuration",
        request=None,
        responses={
            202: OpenApiResponse(
                response=JobResultSerializer,
                description="Job scheduled to generate the router configuration.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to generate a configuration.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The router does not exist."
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="configuration")
    def configuration(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("peering.view_router_configuration"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        job_result = JobResult.enqueue_job(
            generate_configuration,
            "peering.router.generate_configuration",
            Router,
            request.user,
            self.get_object(),
        )
        return Response(
            JobResultSerializer(instance=job_result, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="peering_routers_configure",
        request=RouterConfigureSerializer,
        responses={
            202: OpenApiResponse(
                response=JobResultSerializer,
                description="Job scheduled to generate configure routers.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="Invalid list of routers provided.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to configure routers.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The router does not exist."
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="configure")
    def configure(self, request):
        # Check user permission first
        if not request.user.has_perm("peering.deploy_router_configuration"):
            return Response(None, status=status.HTTP_403_FORBIDDEN)

        # Make sure request is valid
        serializer = RouterConfigureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        router_ids = serializer.validated_data.get("routers")
        if len(router_ids) < 1:
            raise ValidationError("routers list must not be empty")
        commit = serializer.validated_data.get("commit")

        routers = Router.objects.filter(pk__in=router_ids)
        if not routers:
            return Response(status=status.HTTP_404_NOT_FOUND)

        job_results = []
        for router in routers:
            job_result = JobResult.enqueue_job(
                set_napalm_configuration,
                "peering.router.set_napalm_configuration",
                Router,
                request.user,
                router,
                commit,
            )
            job_results.append(job_result)

        return Response(
            JobResultSerializer(
                job_results, many=True, context={"request": request}
            ).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="peering_routers_test_napalm_connection",
        request=RouterConfigureSerializer,
        responses={
            202: OpenApiResponse(
                response=JobResultSerializer,
                description="Job scheduled to test the router NAPALM connection.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The router does not exist."
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="test-napalm-connection")
    def test_napalm_connection(self, request, pk=None):
        job_result = JobResult.enqueue_job(
            test_napalm_connection,
            "peering.router.test_napalm_connection",
            Router,
            request.user,
            self.get_object(),
        )
        return Response(
            JobResultSerializer(instance=job_result, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )


class RoutingPolicyViewSet(ModelViewSet):
    queryset = RoutingPolicy.objects.all()
    serializer_class = RoutingPolicySerializer
    filterset_class = RoutingPolicyFilterSet
