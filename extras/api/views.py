from extras.filters import JobResultFilterSet
from extras.models import JobResult, ServiceReference
from utils.api import ReadOnlyModelViewSet, StaticChoicesViewSet, ModelViewSet

from .serializers import JobResultSerializer, ServiceReferenceSerializer


class ExtrasFieldChoicesViewSet(StaticChoicesViewSet):
    fields = [(JobResult, ["status"])]


class JobResultViewSet(ReadOnlyModelViewSet):
    queryset = JobResult.objects.all()
    serializer_class = JobResultSerializer
    filterset_class = JobResultFilterSet


class ServiceReferenceViewSet(ModelViewSet):
    queryset = ServiceReference.objects.all()
    serializer_class = ServiceReferenceSerializer