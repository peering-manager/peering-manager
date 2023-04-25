from rest_framework.routers import APIRootView

from devices.filters import ConfigurationFilterSet, PlatformFilterSet
from devices.models import Configuration, Platform
from peering_manager.api.viewsets import PeeringManagerModelViewSet

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
