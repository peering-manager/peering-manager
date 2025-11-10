from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from core.api.serializers import JobSerializer
from core.models import Job

from ...jobs import synchronise
from ...models import (
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
from ...sync import PeeringDB


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
                "carrierfac-count": CarrierFacility.objects.count(),
                "fac-count": Facility.objects.count(),
                "ix-count": InternetExchange.objects.count(),
                "ixfac-count": InternetExchangeFacility.objects.count(),
                "ixlan-count": IXLan.objects.count(),
                "ixpfx-count": IXLanPrefix.objects.count(),
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
        job = Job.enqueue(
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
