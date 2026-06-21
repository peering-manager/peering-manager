from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ... import filtersets, models
from .. import serializers

__all__ = ("ScheduledTaskViewSet",)


class ScheduledTaskViewSet(PeeringManagerModelViewSet):
    queryset = models.ScheduledTask.objects.all()
    serializer_class = serializers.ScheduledTaskSerializer
    filterset_class = filtersets.ScheduledTaskFilterSet
