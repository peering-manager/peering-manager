from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from core.api.serializers import JobSerializer
from core.models import Job
from messaging.api.serializers import EmailSendingSerializer
from messaging.models import Email
from peering.models import AutonomousSystem

from ..filtersets import (
    FacilityFilterSet,
    InternetExchangeFacilityFilterSet,
    InternetExchangeFilterSet,
    IXLanFilterSet,
    IXLanPrefixFilterSet,
    NetworkContactFilterSet,
    NetworkFacilityFilterSet,
    NetworkFilterSet,
    NetworkIXLanFilterSet,
    OrganizationFilterSet,
    SynchronisationFilterSet,
)
from ..jobs import synchronise
from ..models import (
    Campus,
    Carrier,
    CarrierFacility,
    Facility,
    InternetExchange,
    InternetExchangeFacility,
    IXLan,
    IXLanPrefix,
    Network,
    NetworkContact,
    NetworkFacility,
    NetworkIXLan,
    Organization,
    Synchronisation,
)
from ..sync import PeeringDB
from .serializers import (
    FacilitySerializer,
    InternetExchangeFacilitySerializer,
    InternetExchangeSerializer,
    IXLanPrefixSerializer,
    IXLanSerializer,
    NetworkContactSerializer,
    NetworkFacilitySerializer,
    NetworkIXLanSerializer,
    NetworkSerializer,
    OrganizationSerializer,
    SynchronisationSerializer,
)


class PeeringDBRootView(APIRootView):
    def get_view_name(self):
        return "PeeringDB"


class CacheViewSet(ViewSet):
    permission_classes = [IsAdminUser]

    def get_view_name(self):
        return "Cache Management"

    @extend_schema(
        operation_id="peeringdb_cache_statistics",
        request=None,
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request):
        return Response(
            {
                "campus-count": Campus.objects.count(),
                "carrier-count": Carrier.objects.count(),
                "carrierfac": CarrierFacility.objects.count(),
                "fac-count": Facility.objects.count(),
                "ix-count": InternetExchange.objects.count(),
                "ixfac-count": InternetExchangeFacility.objects.count(),
                "ixlan-count": IXLan.objects.count(),
                "ixlanpfx-count": IXLanPrefix.objects.count(),
                "net-count": Network.objects.count(),
                "poc-count": NetworkContact.objects.count(),
                "netfac-count": NetworkFacility.objects.count(),
                "netixlan-count": NetworkIXLan.objects.count(),
                "org-count": Organization.objects.count(),
                "sync-count": Synchronisation.objects.count(),
            }
        )

    @extend_schema(
        operation_id="peeringdb_cache_update",
        request=None,
        responses={202: JobSerializer},
    )
    @action(detail=False, methods=["post"], url_path="update-local")
    def update_local(self, request):
        job = Job.enqueue_job(
            synchronise,
            name="peeringdb.synchronise",
            object_model=Synchronisation,
            user=request.user,
        )
        return Response(
            JobSerializer(instance=job, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="peeringdb_cache_clear",
        request=None,
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=["post"], url_path="clear-local")
    def clear_local(self, request):
        PeeringDB().clear_local_database()
        return Response({"status": "success"})


class FacilityViewSet(ReadOnlyModelViewSet):
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
    filterset_class = FacilityFilterSet


class InternetExchangeViewSet(ReadOnlyModelViewSet):
    queryset = InternetExchange.objects.all()
    serializer_class = InternetExchangeSerializer
    filterset_class = InternetExchangeFilterSet


class InternetExchangeFacilityViewSet(ReadOnlyModelViewSet):
    queryset = InternetExchangeFacility.objects.all()
    serializer_class = InternetExchangeFacilitySerializer
    filterset_class = InternetExchangeFacilityFilterSet


class IXLanViewSet(ReadOnlyModelViewSet):
    queryset = IXLan.objects.all()
    serializer_class = IXLanSerializer
    filterset_class = IXLanFilterSet


class IXLanPrefixViewSet(ReadOnlyModelViewSet):
    queryset = IXLanPrefix.objects.all()
    serializer_class = IXLanPrefixSerializer
    filterset_class = IXLanPrefixFilterSet


class NetworkViewSet(ReadOnlyModelViewSet):
    queryset = Network.objects.all()
    serializer_class = NetworkSerializer
    filterset_class = NetworkFilterSet

    @extend_schema(
        operation_id="peeringdb_networks_render_email",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="Renders the e-mail template."
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.NONE,
                description="The network or e-mail template does not exist.",
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="render-email")
    def render_email(self, request, pk=None):
        # Make sure request is valid
        serializer = EmailSendingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            template = Email.objects.get(pk=serializer.validated_data.get("email"))
            autonomous_system = AutonomousSystem.objects.get(
                pk=serializer.validated_data.get("autonomous_system")
            )
            network = Network.objects.get(pk=serializer.validated_data.get("network"))
            rendered = network.render_email(template, autonomous_system)
            return Response(data={"subject": rendered[0], "body": rendered[1]})
        except Email.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class NetworkContactViewSet(ReadOnlyModelViewSet):
    queryset = NetworkContact.objects.all()
    serializer_class = NetworkContactSerializer
    filterset_class = NetworkContactFilterSet


class NetworkFacilityViewSet(ReadOnlyModelViewSet):
    queryset = NetworkFacility.objects.all()
    serializer_class = NetworkFacilitySerializer
    filterset_class = NetworkFacilityFilterSet


class NetworkIXLanViewSet(ReadOnlyModelViewSet):
    queryset = NetworkIXLan.objects.all()
    serializer_class = NetworkIXLanSerializer
    filterset_class = NetworkIXLanFilterSet


class OrganizationViewSet(ReadOnlyModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    filterset_class = OrganizationFilterSet


class SynchronisationViewSet(ReadOnlyModelViewSet):
    queryset = Synchronisation.objects.all()
    serializer_class = SynchronisationSerializer
    filterset_class = SynchronisationFilterSet
