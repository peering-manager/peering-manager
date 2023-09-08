from peering_manager.api.serializers import PeeringManagerModelSerializer

from ..models import Configuration, Platform
from .nested_serializers import *

__all__ = ("ConfigurationSerializer", "PlatformSerializer")


class ConfigurationSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = Configuration
        fields = [
            "id",
            "display",
            "name",
            "description",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
            "comments",
            "tags",
            "created",
            "updated",
        ]


class PlatformSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = Platform
        fields = [
            "id",
            "display",
            "name",
            "slug",
            "description",
            "password_algorithm",
            "napalm_driver",
            "napalm_args",
            "tags",
            "created",
            "updated",
        ]
