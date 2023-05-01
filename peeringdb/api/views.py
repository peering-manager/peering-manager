from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from core.api.serializers import JobSerializer
from core.models import Job
from peeringdb.filters import NetworkFilterSet, SynchronisationFilterSet
from peeringdb.jobs import synchronise
from peeringdb.models import (
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
from peeringdb.sync import PeeringDB
from utils.api import get_serializer_for_model

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


class InternetExchangeViewSet(ReadOnlyModelViewSet):
    queryset = InternetExchange.objects.all()
    serializer_class = InternetExchangeSerializer


class InternetExchangeFacilityViewSet(ReadOnlyModelViewSet):
    queryset = InternetExchangeFacility.objects.all()
    serializer_class = InternetExchangeFacilitySerializer


class IXLanViewSet(ReadOnlyModelViewSet):
    queryset = IXLan.objects.all()
    serializer_class = IXLanSerializer


class IXLanPrefixViewSet(ReadOnlyModelViewSet):
    queryset = IXLanPrefix.objects.all()
    serializer_class = IXLanPrefixSerializer


class NetworkViewSet(ReadOnlyModelViewSet):
    queryset = Network.objects.all()
    serializer_class = NetworkSerializer
    filterset_class = NetworkFilterSet


class NetworkContactViewSet(ReadOnlyModelViewSet):
    queryset = NetworkContact.objects.all()
    serializer_class = NetworkContactSerializer


class NetworkFacilityViewSet(ReadOnlyModelViewSet):
    queryset = NetworkFacility.objects.all()
    serializer_class = NetworkFacilitySerializer


class NetworkIXLanViewSet(ReadOnlyModelViewSet):
    queryset = NetworkIXLan.objects.all()
    serializer_class = NetworkIXLanSerializer


class OrganizationViewSet(ReadOnlyModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class SynchronisationViewSet(ReadOnlyModelViewSet):
    queryset = Synchronisation.objects.all()
    serializer_class = SynchronisationSerializer
    filterset_class = SynchronisationFilterSet
