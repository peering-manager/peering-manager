from rest_framework.viewsets import ReadOnlyModelViewSet

from ... import filtersets, models
from .. import serializers


class JobViewSet(ReadOnlyModelViewSet):
    """
    Retrieve a list of jobs.
    """

    queryset = models.Job.objects.prefetch_related("user")
    serializer_class = serializers.JobSerializer
    filterset_class = filtersets.JobFilterSet
