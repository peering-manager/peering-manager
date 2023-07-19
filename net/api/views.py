from rest_framework.routers import APIRootView

from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ..filtersets import ConnectionFilterSet
from ..models import Connection
from .serializers import ConnectionSerializer


class NetRootView(APIRootView):
    def get_view_name(self):
        return "Net"


class ConnectionViewSet(PeeringManagerModelViewSet):
    queryset = Connection.objects.all()
    serializer_class = ConnectionSerializer
    filterset_class = ConnectionFilterSet
