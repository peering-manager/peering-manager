from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from peering_manager.api.viewsets import (
    PeeringManagerModelViewSet,
    PeeringManagerReadOnlyModelViewSet,
)
from utils.functions import count_related

from ... import filtersets, models
from .. import serializers

__all__ = ("DataFileViewSet", "DataSourceViewSet")


class DataFileViewSet(PeeringManagerReadOnlyModelViewSet):
    queryset = models.DataFile.objects.defer("data").prefetch_related("source")
    serializer_class = serializers.DataFileSerializer
    filterset_class = filtersets.DataFileFilterSet


class DataSourceViewSet(PeeringManagerModelViewSet):
    queryset = models.DataSource.objects.annotate(
        file_count=count_related(models.DataFile, "source")
    )
    serializer_class = serializers.DataSourceSerializer
    filterset_class = filtersets.DataSourceFilterSet

    @action(detail=True, methods=["post"])
    def synchronise(self, request, pk):
        if not request.user.has_perm("core.synchronise_datasource"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        instance = self.get_object()
        job = instance.enqueue_synchronisation_job(request)

        return Response(
            serializers.JobSerializer(instance=job, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )
