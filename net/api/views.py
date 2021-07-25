from net.filters import ConnectionFilterSet
from net.models import Connection
from peering_manager.api.views import ModelViewSet

from .serializers import ConnectionSerializer


class ConnectionViewSet(ModelViewSet):
    queryset = Connection.objects.all()
    serializer_class = ConnectionSerializer
    filterset_class = ConnectionFilterSet
