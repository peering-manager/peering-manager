from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response

from .serializers import SynchronizationSerializer
from peeringdb.filters import SynchronizationFilter
from peeringdb.models import Synchronization


class SynchronizationViewSet(ReadOnlyModelViewSet):
    queryset = Synchronization.objects.all()
    serializer_class = SynchronizationSerializer
    filterset_class = SynchronizationFilter
