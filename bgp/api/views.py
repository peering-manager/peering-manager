from rest_framework.routers import APIRootView

from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ..filtersets import RelationshipFilterSet
from ..models import Relationship
from .serializers import RelationshipSerializer


class BGPRootView(APIRootView):
    def get_view_name(self):
        return "BGP"


class RelationshipViewSet(PeeringManagerModelViewSet):
    queryset = Relationship.objects.all()
    serializer_class = RelationshipSerializer
    filterset_class = RelationshipFilterSet
