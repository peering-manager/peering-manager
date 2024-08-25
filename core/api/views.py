from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.viewsets import ReadOnlyModelViewSet

from peering_manager.api.viewsets import (
    PeeringManagerModelViewSet,
    PeeringManagerReadOnlyModelViewSet,
)
from utils.functions import count_related

from .. import filtersets, models
from . import serializers


class CoreRootView(APIRootView):
    """
    Core API root view.
    """

    def get_view_name(self):
        return "Core"


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


class JobViewSet(ReadOnlyModelViewSet):
    """
    Retrieve a list of jobs.
    """

    queryset = models.Job.objects.prefetch_related("user")
    serializer_class = serializers.JobSerializer
    filterset_class = filtersets.JobFilterSet


class ObjectChangeViewSet(PeeringManagerModelViewSet):
    queryset = models.ObjectChange.objects.all()
    serializer_class = serializers.ObjectChangeSerializer
    filterset_class = filtersets.ObjectChangeFilterSet
