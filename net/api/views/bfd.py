from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ...filtersets import BFDFilterSet
from ...models import BFD
from ..serializers import BFDSerializer

__all__ = ("BFDViewSet",)


class BFDViewSet(PeeringManagerModelViewSet):
    queryset = BFD.objects.all()
    serializer_class = BFDSerializer
    filterset_class = BFDFilterSet
