from rest_framework.routers import APIRootView

from devices.filters import ConfigurationFilterSet, PlatformFilterSet
from devices.models import Configuration, Platform
from peering_manager.api.views import ModelViewSet

from .serializers import ConfigurationSerializer, PlatformSerializer


class DevicesRootView(APIRootView):
    def get_view_name(self):
        return "Devices"


class ConfigurationViewSet(ModelViewSet):
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer
    filterset_class = ConfigurationFilterSet


class PlatformViewSet(ModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    filterset_class = PlatformFilterSet
