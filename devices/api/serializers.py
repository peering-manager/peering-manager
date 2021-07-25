from devices.models import Platform
from peering_manager.api.serializers import PrimaryModelSerializer

from .nested_serializers import *

__all__ = ("NestedPlatformSerializer", "PlatformSerializer")


class PlatformSerializer(PrimaryModelSerializer):
    class Meta:
        model = Platform
        fields = [
            "id",
            "name",
            "slug",
            "napalm_driver",
            "napalm_args",
            "password_algorithm",
            "description",
        ]
