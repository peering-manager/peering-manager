from rest_framework.serializers import ModelSerializer

from devices.models import Platform

from .nested_serializers import *


class PlatformSerializer(ModelSerializer):
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
