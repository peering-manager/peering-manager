from rest_framework.routers import APIRootView

from devices.filters import PlatformFilterSet
from devices.models import Platform
from peering_manager.api.views import ModelViewSet

from .serializers import PlatformSerializer


class DevicesRootView(APIRootView):
    def get_view_name(self):
        return "Devices"


class PlatformViewSet(ModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    filterset_class = PlatformFilterSet
