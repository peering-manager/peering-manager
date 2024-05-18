from rest_framework import serializers

from peering.api.nested_serializers import NestedAutonomousSystemSerializer
from peering_manager.api.fields import ChoiceField
from peering_manager.api.serializers import PeeringManagerModelSerializer

from ..enums import DeviceStatus
from ..models import Configuration, Platform, Router
from .nested_serializers import *

__all__ = ("ConfigurationSerializer", "PlatformSerializer", "RouterSerializer")


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


class RouterSerializer(PeeringManagerModelSerializer):
    poll_bgp_sessions_last_updated = serializers.DateTimeField(read_only=True)
    configuration_template = NestedConfigurationSerializer(required=False)
    local_autonomous_system = NestedAutonomousSystemSerializer()
    platform = NestedPlatformSerializer()
    status = ChoiceField(required=False, choices=DeviceStatus)

    class Meta:
        model = Router
        fields = [
            "id",
            "display",
            "name",
            "hostname",
            "platform",
            "status",
            "encrypt_passwords",
            "poll_bgp_sessions_state",
            "poll_bgp_sessions_last_updated",
            "configuration_template",
            "local_autonomous_system",
            "netbox_device_id",
            "local_context_data",
            "napalm_username",
            "napalm_password",
            "napalm_timeout",
            "napalm_args",
            "comments",
            "tags",
            "created",
            "updated",
        ]


class RouterConfigureSerializer(serializers.Serializer):
    routers = serializers.ListField(child=serializers.IntegerField())
    commit = serializers.BooleanField(required=False, default=False)
