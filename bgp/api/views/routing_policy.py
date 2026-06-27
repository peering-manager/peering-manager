from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ...filtersets import RoutingPolicyFilterSet
from ...models import RoutingPolicy
from ..serializers import RoutingPolicySerializer

__all__ = ("RoutingPolicyViewSet",)


class RoutingPolicyViewSet(PeeringManagerModelViewSet):
    queryset = RoutingPolicy.objects.all()
    serializer_class = RoutingPolicySerializer
    filterset_class = RoutingPolicyFilterSet
