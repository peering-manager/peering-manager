from extras.filters import JobResultFilterSet
from extras.models import JobResult
from utils.api import ReadOnlyModelViewSet, StaticChoicesViewSet

from .serializers import JobResultSerializer


class ExtrasFieldChoicesViewSet(StaticChoicesViewSet):
    fields = [(JobResult, ["status"])]


class JobResultViewSet(ReadOnlyModelViewSet):
    queryset = JobResult.objects.all()
    serializer_class = JobResultSerializer
    filterset_class = JobResultFilterSet
