from rest_framework.routers import APIRootView

from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ..filtersets import ConfigurationFilterSet, PlatformFilterSet
from ..models import Configuration, Platform
from .serializers import ConfigurationSerializer, PlatformSerializer


class DevicesRootView(APIRootView):
    def get_view_name(self):
        return "Devices"


class ConfigurationViewSet(PeeringManagerModelViewSet):
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer
    filterset_class = ConfigurationFilterSet


class PlatformViewSet(PeeringManagerModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    filterset_class = PlatformFilterSet
