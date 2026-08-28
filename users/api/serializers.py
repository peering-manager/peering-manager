from django.contrib.auth.models import Group, User
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from peering_manager.api.fields import SerializedPKRelatedField
from peering_manager.api.serializers import ValidatedModelSerializer

from .nested_serializers import *

__all__ = ("GroupSerializer", "UserSerializer")


class UserSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="users-api:user-detail")
    groups = SerializedPKRelatedField(
        queryset=Group.objects.all(),
        serializer=NestedGroupSerializer,
        required=False,
        many=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "url",
            "display",
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_active",
            "date_joined",
            "groups",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def _set_password(self, user: User, password: str | None) -> User:
        """
        Set the password apart from the other fields, which stores its hash and not
        the password itself.
        """
        if password is not None:
            user.set_password(password)
            user.save()

        return user

    def create(self, validated_data):
        password = validated_data.pop("password")
        return self._set_password(super().create(validated_data), password)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        return self._set_password(super().update(instance, validated_data), password)

    @extend_schema_field(OpenApiTypes.STR)
    def get_display(self, o):
        if full_name := o.get_full_name():
            return f"{o.username} ({full_name})"
        return o.username


class GroupSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="users-api:group-detail")
    user_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = ["id", "url", "display", "name", "user_count"]
