from django.http import HttpResponseForbidden

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from .serializers import SynchronizationSerializer
from peeringdb.filters import SynchronizationFilter
from peeringdb.http import PeeringDB
from peeringdb.models import Synchronization


class CacheViewSet(ViewSet):
    # Required for DRF
    queryset = Synchronization.objects.none()

    @action(detail=False, methods=["post", "put", "patch"], url_path="update-local")
    def update_local(self, request):
        # Not member from staff, don't allow cache management
        if not request.user.is_staff and not request.user.is_superuser:
            return HttpResponseForbidden()

        api = PeeringDB()
        synchronization = api.update_local_database(api.get_last_sync_time())

        return Response(
            {"synchronization": SynchronizationSerializer(synchronization).data}
        )

    @action(detail=False, methods=["delete"], url_path="clear-local")
    def clear_local(self, request):
        # Not member from staff, don't allow cache management
        if not request.user.is_staff and not request.user.is_superuser:
            return HttpResponseForbidden()

        PeeringDB().clear_local_database()
        return Response({"status": "success"})

    @action(
        detail=False, methods=["post", "put", "patch"], url_path="index-peer-records"
    )
    def index_peer_records(self, request):
        # Not member from staff, don't allow cache management
        if not request.user.is_staff and not request.user.is_superuser:
            return HttpResponseForbidden()

        PeeringDB().force_peer_records_discovery()
        return Response({"status": "success"})


class SynchronizationViewSet(ReadOnlyModelViewSet):
    queryset = Synchronization.objects.all()
    serializer_class = SynchronizationSerializer
    filterset_class = SynchronizationFilter
