from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ...filtersets import CommunityFilterSet
from ...models import Community
from ..serializers import CommunitySerializer

__all__ = ("CommunityViewSet",)


class CommunityViewSet(PeeringManagerModelViewSet):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    filterset_class = CommunityFilterSet
