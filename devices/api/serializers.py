from devices.models import Platform
from peering_manager.api import PrimaryModelSerializer

from .nested_serializers import *

__all__ = (
    "ConfigurationSerializer",
    "NestedConfigurationSerializer",
    "PlatformSerializer",
    "NestedPlatformSerializer",
)


class ConfigurationSerializer(PrimaryModelSerializer):
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


class PlatformSerializer(PrimaryModelSerializer):
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
