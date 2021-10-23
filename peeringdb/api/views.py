from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from extras.models import JobResult
from peeringdb.filters import NetworkFilterSet, SynchronizationFilterSet
from peeringdb.jobs import synchronize
from peeringdb.models import (
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
    Synchronization,
)
from peeringdb.sync import PeeringDB
from utils.functions import get_serializer_for_model

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
    SynchronizationSerializer,
)


class CacheViewSet(ViewSet):
    permission_classes = [IsAdminUser]

    def get_view_name(self):
        return "Cache Management"

    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request):
        return Response(
            {
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
                "sync-count": Synchronization.objects.count(),
            }
        )

    @action(detail=False, methods=["post"], url_path="update-local")
    def update_local(self, request):
        job_result = JobResult.enqueue_job(
            synchronize, "peeringdb.synchronize", Synchronization, request.user
        )
        serializer = get_serializer_for_model(JobResult)

        return Response(
            serializer(instance=job_result, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
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


class SynchronizationViewSet(ReadOnlyModelViewSet):
    queryset = Synchronization.objects.all()
    serializer_class = SynchronizationSerializer
    filterset_class = SynchronizationFilterSet
