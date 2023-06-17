from rest_framework.routers import APIRootView

from peering_manager.api.viewsets import PeeringManagerModelViewSet
from utils.filters import ObjectChangeFilterSet
from utils.models import ObjectChange

from .serializers import ObjectChangeSerializer


class UtilsRootView(APIRootView):
    def get_view_name(self):
        return "Utilities"


class ObjectChangeViewSet(PeeringManagerModelViewSet):
    queryset = ObjectChange.objects.all()
    serializer_class = ObjectChangeSerializer
    filterset_class = ObjectChangeFilterSet
