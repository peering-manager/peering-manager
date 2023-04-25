from rest_framework.routers import APIRootView

from net.filters import ConnectionFilterSet
from net.models import Connection
from peering_manager.api.viewsets import PeeringManagerModelViewSet

from .serializers import ConnectionSerializer


class NetRootView(APIRootView):
    def get_view_name(self):
        return "Net"


class ConnectionViewSet(PeeringManagerModelViewSet):
    queryset = Connection.objects.all()
    serializer_class = ConnectionSerializer
    filterset_class = ConnectionFilterSet
