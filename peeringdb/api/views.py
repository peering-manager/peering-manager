from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from .serializers import (
    PeerRecordSerializer,
    SynchronizationSerializer,
    ContactSerializer,
    NetworkSerializer,
)
from peeringdb.filters import (
    PeerRecordFilterSet,
    SynchronizationFilterSet,
    ContactFilterSet,
    NetworkFilterSet,
)
from peeringdb.http import PeeringDB
from peeringdb.models import Contact, Network, NetworkIXLAN, PeerRecord, Synchronization

from utils.api import ModelViewSet


class CacheViewSet(ViewSet):
    permission_classes = [IsAdminUser]

    def get_view_name(self):
        return "Cache Management"

    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request):
        return Response(
            {
                "contact-count": Contact.objects.count(),
                "network-count": Network.objects.count(),
                "network-ixlan-count": NetworkIXLAN.objects.count(),
                "peer-record-count": PeerRecord.objects.count(),
            }
        )

    @action(detail=False, methods=["post", "put", "patch"], url_path="update-local")
    def update_local(self, request):
        api = PeeringDB()
        synchronization = api.update_local_database(api.get_last_sync_time())

        return Response(
            {"synchronization": SynchronizationSerializer(synchronization).data}
        )

    @action(detail=False, methods=["post"], url_path="clear-local")
    def clear_local(self, request):
        PeeringDB().clear_local_database()
        return Response({"status": "success"})

    @action(
        detail=False, methods=["post", "put", "patch"], url_path="index-peer-records"
    )
    def index_peer_records(self, request):
        return Response(
            {"peer-record-count": PeeringDB().force_peer_records_discovery()}
        )


class ContactsViewSet(ReadOnlyModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filterset_class = ContactFilterSet


class NetworksViewSet(ReadOnlyModelViewSet):
    queryset = Network.objects.all()
    serializer_class = NetworkSerializer
    filterset_class = NetworkFilterSet


class PeerRecordViewSet(ModelViewSet):
    queryset = PeerRecord.objects.all()
    serializer_class = PeerRecordSerializer
    filterset_class = PeerRecordFilterSet


class SynchronizationViewSet(ReadOnlyModelViewSet):
    queryset = Synchronization.objects.all()
    serializer_class = SynchronizationSerializer
    filterset_class = SynchronizationFilterSet
