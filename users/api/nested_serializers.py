from django.contrib.auth.models import Group, User
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from peering_manager.api.serializers import WritableNestedSerializer

__all__ = ("NestedGroupSerializer", "NestedUserSerializer")


class NestedGroupSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="users-api:group-detail")

    class Meta:
        model = Group
        fields = ["id", "url", "display", "name"]


class NestedUserSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="users-api:user-detail")

    class Meta:
        model = User
        fields = ["id", "url", "display", "username"]

    @extend_schema_field(OpenApiTypes.STR)
    def get_display(self, o):
        if full_name := o.get_full_name():
            return f"{o.username} ({full_name})"
        return o.username
