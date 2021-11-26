from rest_framework.routers import APIRootView

from bgp.api.serializers import RelationshipSerializer
from bgp.filters import RelationshipFilterSet
from bgp.models import Relationship
from peering_manager.api.views import ModelViewSet


class BGPRootView(APIRootView):
    def get_view_name(self):
        return "BGP"


class RelationshipViewSet(ModelViewSet):
    queryset = Relationship.objects.all()
    serializer_class = RelationshipSerializer
    filterset_class = RelationshipFilterSet
