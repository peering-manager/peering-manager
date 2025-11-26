from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ...filtersets import RelationshipFilterSet
from ...models import Relationship
from ..serializers import RelationshipSerializer

__all__ = ("RelationshipViewSet",)


class RelationshipViewSet(PeeringManagerModelViewSet):
    queryset = Relationship.objects.all()
    serializer_class = RelationshipSerializer
    filterset_class = RelationshipFilterSet
