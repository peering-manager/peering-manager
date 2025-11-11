from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ...filtersets import HiddenPeerFilterSet
from ...models import HiddenPeer
from ..serializers import HiddenPeerSerializer

__all__ = ("HiddenPeerViewSet",)


class HiddenPeerViewSet(PeeringManagerModelViewSet):
    queryset = HiddenPeer.objects.all()
    serializer_class = HiddenPeerSerializer
    filterset_class = HiddenPeerFilterSet
