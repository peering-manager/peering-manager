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
from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ..enums import DeviceStatus
from ..filtersets import ConfigurationFilterSet, PlatformFilterSet, RouterFilterSet
from ..jobs import (
    poll_bgp_sessions,
    push_configuration_to_data_source,
    render_configuration,
    set_napalm_configuration,
    test_napalm_connection,
)
from ..models import Configuration, Platform, Router
from .serializers import (
    ConfigurationSerializer,
    PlatformSerializer,
    RouterConfigureSerializer,
    RouterSerializer,
)


class DevicesRootView(APIRootView):
    def get_view_name(self):
        return "Devices"


class ConfigurationViewSet(PeeringManagerModelViewSet):
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer
    filterset_class = ConfigurationFilterSet


class PlatformViewSet(PeeringManagerModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    filterset_class = PlatformFilterSet


class RouterViewSet(PeeringManagerModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    filterset_class = RouterFilterSet

    @extend_schema(
        operation_id="devices_routers_configuration",
        responses={
            202: OpenApiResponse(
                response=JobSerializer,
                description="Job scheduled to render the router configuration.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to render a configuration.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The router does not exist."
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="configuration")
    def configuration(self, request, pk=None):
        # Check user permission first
        if not request.user.has_perm("devices.view_router_configuration"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        router = self.get_object()
        job = Job.enqueue(
            render_configuration,
            router,
            name="devices.router.render_configuration",
            object=router,
            user=request.user,
        )
        return Response(
            JobSerializer(instance=job, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="devices_routers_configure",
        request=RouterConfigureSerializer,
        responses={
            202: OpenApiResponse(
                response=JobSerializer,
                description="Job scheduled to render configure routers.",
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
        if not request.user.has_perm("devices.deploy_router_configuration"):
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
                name="devices.router.set_napalm_configuration",
                object=router,
                user=request.user,
            )
            jobs.append(job)

        return Response(
            JobSerializer(jobs, many=True, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="devices_routers_poll_bgp_sessions",
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
            name="devices.router.poll_bgp_sessions",
            object=router,
            user=request.user,
        )
        return Response(
            data=JobSerializer(instance=job, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="devices_routers_test_napalm_connection",
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
            name="devices.router.test_napalm_connection",
            object=router,
            user=request.user,
        )
        return Response(
            JobSerializer(instance=job, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="devices_routers_update_from_netbox",
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
            not request.user.has_perm("devices.add_router")
            or not request.user.has_perm("devices.change_router")
            or not request.user.has_perm("devices.delete_router")
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
            tags = {t.slug for t in data["tags"]}
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

        router.platform = platform
        router.status = device_status
        router.save()
        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="devices_routers_push_datasource",
        request=RouterConfigureSerializer,
        responses={
            202: OpenApiResponse(
                response=JobSerializer,
                description="Job scheduled to push router configurations to data sources.",
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="Invalid list of routers provided.",
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The user does not have the permission to push router configurations to data sources.",
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="The router does not exist."
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="push-datasource")
    def push_datasource(self, request):
        # Check user permission first
        if not request.user.has_perm(
            "devices.push_router_configuration_to_data_source"
        ):
            return Response(None, status=status.HTTP_403_FORBIDDEN)

        # Make sure request is valid
        serializer = RouterConfigureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        router_ids = serializer.validated_data.get("routers")
        if len(router_ids) < 1:
            raise ValidationError("routers list must not be empty")

        routers = Router.objects.filter(pk__in=router_ids)
        if not routers:
            return Response(status=status.HTTP_404_NOT_FOUND)

        jobs = []
        for router in routers:
            job = Job.enqueue(
                push_configuration_to_data_source,
                router,
                name="devices.router.push_to_data_source",
                object=router,
                user=request.user,
            )
            jobs.append(job)

        return Response(
            JobSerializer(jobs, many=True, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )
