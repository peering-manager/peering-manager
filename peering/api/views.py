from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.routers import APIRootView

from core.api.serializers import JobSerializer
from core.models import Job
from devices.models import Platform
from messaging.api.serializers import EmailSendingSerializer
from messaging.models import Email
from peering_manager.api.exceptions import ServiceUnavailable
from peering_manager.api.viewsets import PeeringManagerModelViewSet
from peeringdb.api.serializers import NetworkIXLanSerializer

from ..enums import DeviceStatus
from ..filtersets import (
    AutonomousSystemFilterSet,
    BGPGroupFilterSet,
    CommunityFilterSet,
    DirectPeeringSessionFilterSet,
    InternetExchangeFilterSet,
    InternetExchangePeeringSessionFilterSet,
    RouterFilterSet,
    RoutingPolicyFilterSet,
)
from ..jobs import (
    generate_configuration,
    import_sessions_to_internet_exchange,
    poll_bgp_sessions,
    set_napalm_configuration,
    test_napalm_connection,
)
from ..models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from .serializers import (
    AutonomousSystemSerializer,
    BGPGroupSerializer,
    CommunitySerializer,
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


class AutonomousSystemViewSet(PeeringManagerModelViewSet):
    queryset = AutonomousSystem.objects.defer("prefixes")
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
                    name="peering.router.poll_bgp_sessions",
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
            raise ServiceUnavailable("User did not choose an affiliated AS.")

        return Response(
            data=NestedInternetExchangeSerializer(
                self.get_object().get_shared_internet_exchange_points(affiliated),
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
                    name="peering.router.poll_bgp_sessions",
                    object=router,
                    user=request.user,
                )
            )
        return Response(
            JobSerializer(jobs, many=True, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )


class CommunityViewSet(PeeringManagerModelViewSet):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    filterset_class = CommunityFilterSet


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
                    name="peering.router.poll_bgp_sessions",
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


class RouterViewSet(PeeringManagerModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    filterset_class = RouterFilterSet

    @extend_schema(
        operation_id="peering_routers_configuration",
        responses={
            202: OpenApiResponse(
                response=JobSerializer,
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

        router = self.get_object()
        job = Job.enqueue(
            generate_configuration,
            router,
            name="peering.router.generate_configuration",
            object=router,
            user=request.user,
        )
        return Response(
            JobSerializer(instance=job, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="peering_routers_configure",
        request=RouterConfigureSerializer,
        responses={
            202: OpenApiResponse(
                response=JobSerializer,
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

        jobs = []
        for router in routers:
            job = Job.enqueue(
                set_napalm_configuration,
                router,
                commit,
                name="peering.router.set_napalm_configuration",
                object=router,
                user=request.user,
            )
            jobs.append(job)

        return Response(
            JobSerializer(jobs, many=True, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="peering_routers_poll_bgp_sessions",
        responses={
            202: OpenApiResponse(
                response=JobSerializer,
                description="Job scheduled to poll BGP sessions.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to poll BGP sessions state.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The router does not exist.",
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

        router = self.get_object()
        job = Job.enqueue(
            poll_bgp_sessions,
            router,
            name="peering.router.poll_bgp_sessions",
            object=router,
            user=request.user,
        )
        return Response(
            data=JobSerializer(instance=job, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="peering_routers_test_napalm_connection",
        request=RouterConfigureSerializer,
        responses={
            202: OpenApiResponse(
                response=JobSerializer,
                description="Job scheduled to test the router NAPALM connection.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The router does not exist."
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="test-napalm-connection")
    def test_napalm_connection(self, request, pk=None):
        router = self.get_object()
        job = Job.enqueue(
            test_napalm_connection,
            router,
            name="peering.router.test_napalm_connection",
            object=router,
            user=request.user,
        )
        return Response(
            JobSerializer(instance=job, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="peering_routers_update_from_netbox",
        request=OpenApiTypes.OBJECT,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="NetBox webhook has been processed successfully.",
            ),
            201: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The device creation has been processed successfully.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The webhook body did not have the required data to take action.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to manage devices.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The device given in the webhook cannot be found.",
            ),
            501: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The device platform in the webhook does not match an avilable platform.",
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="update-from-netbox")
    def update_from_netbox(self, request):
        # Check user permission first
        if (
            not request.user.has_perm("peering.add_router")
            or not request.user.has_perm("peering.change_router")
            or not request.user.has_perm("peering.delete_router")
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            event = request.data["event"]
            data = request.data["data"]
        except KeyError:
            # Fail if we do not find required keys
            return Response(status=status.HTTP_400_BAD_REQUEST)

        for i in (
            "id",
            "device_role",
            "local_context_data",
            "name",
            "platform",
            "status",
        ):
            if i not in data:
                # Fail if we do not find required keys
                return Response(status=status.HTTP_400_BAD_REQUEST)

        # Fail if not in device roles and/or not with correct tag(s)
        if (
            settings.NETBOX_DEVICE_ROLES
            and data["device_role"]["slug"] not in settings.NETBOX_DEVICE_ROLES
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if settings.NETBOX_TAGS:
            tags = set([t.slug for t in data["tags"]])
            if not tags.intersection(settings.NETBOX_TAGS):
                return Response(status=status.HTTP_400_BAD_REQUEST)

        if event == "deleted":
            try:
                number, _ = Router.objects.get(netbox_device_id=data["id"]).delete()
            except Router.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(
                status=status.HTTP_200_OK if number == 1 else status.HTTP_404_NOT_FOUND
            )

        try:
            # Platform slugs must be the same in NetBox and Peering Manager
            platform = Platform.objects.get(slug=data["platform"]["slug"])
        except Platform.DoesNotExist:
            # If platform does not exist, we can proceed
            return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
        # Map NetBox status to Peering Manager's
        device_status = (
            DeviceStatus.ENABLED
            if data["status"]["value"] == "active"
            else DeviceStatus.DISABLED
        )

        router, created = Router.objects.get_or_create(
            netbox_device_id=data["id"],
            defaults={
                "netbox_device_id": data["id"],
                "name": data["name"],
                "hostname": data["name"],
                "status": device_status,
                "platform": platform,
                "local_context_data": data["local_context_data"],
            },
        )

        if created:
            return Response(status=status.HTTP_201_CREATED)
        else:
            router.platform = platform
            router.status = device_status
            router.save()
            return Response(status=status.HTTP_200_OK)


class RoutingPolicyViewSet(PeeringManagerModelViewSet):
    queryset = RoutingPolicy.objects.all()
    serializer_class = RoutingPolicySerializer
    filterset_class = RoutingPolicyFilterSet
