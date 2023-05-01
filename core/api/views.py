from rest_framework.routers import APIRootView
from rest_framework.viewsets import ReadOnlyModelViewSet

from .. import filtersets
from ..models import *
from . import serializers


class CoreRootView(APIRootView):
    """
    Core API root view.
    """

    def get_view_name(self):
        return "Core"


class JobViewSet(ReadOnlyModelViewSet):
    """
    Retrieve a list of jobs.
    """

    queryset = Job.objects.prefetch_related("user")
    serializer_class = serializers.JobSerializer
    filterset_class = filtersets.JobFilterSet
