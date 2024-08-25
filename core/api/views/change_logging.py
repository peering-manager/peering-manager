from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ... import filtersets, models
from .. import serializers


class ObjectChangeViewSet(PeeringManagerModelViewSet):
    queryset = models.ObjectChange.objects.all()
    serializer_class = serializers.ObjectChangeSerializer
    filterset_class = filtersets.ObjectChangeFilterSet
