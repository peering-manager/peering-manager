from devices.models import Platform
from peering_manager.api.serializers import PeeringManagerModelSerializer

from .nested_serializers import *

__all__ = (
    "ConfigurationSerializer",
    "NestedConfigurationSerializer",
    "PlatformSerializer",
    "NestedPlatformSerializer",
)


class ConfigurationSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = Configuration
        fields = [
            "id",
            "display",
            "name",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
            "comments",
            "tags",
        ]


class PlatformSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = Platform
        fields = [
            "id",
            "display",
            "name",
            "slug",
            "napalm_driver",
            "napalm_args",
            "password_algorithm",
            "description",
        ]
