from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from peering_manager.api.fields import SerializedPKRelatedField
from peering_manager.api.serializers import ValidatedModelSerializer
from users.models import TokenObjectPermission

from .nested_serializers import *

__all__ = ("GroupSerializer", "TokenObjectPermissionSerializer", "UserSerializer")


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

    def create(self, validated_data):
        """
        Extract the password from validated data and set it separately to ensure
        proper hash generation.
        """
        password = validated_data.pop("password")
        user = super().create(validated_data)
        user.set_password(password)
        user.save()

        return user

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


class TokenObjectPermissionSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="users-api:tokenobjectpermission-detail"
    )
    token = serializers.PrimaryKeyRelatedField(
        queryset=__import__("users.models", fromlist=["Token"]).Token.objects.all()
    )
    content_type = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all()
    )
    object_type = serializers.SerializerMethodField()
    object_repr = serializers.SerializerMethodField()

    class Meta:
        model = TokenObjectPermission
        fields = [
            "id",
            "url",
            "display",
            "token",
            "content_type",
            "object_type",
            "object_id",
            "object_repr",
            "can_view",
            "can_edit",
            "can_delete",
            "custom_actions",
            "constraints",
            "created",
            "last_updated",
        ]
        read_only_fields = ["created", "last_updated"]

    @extend_schema_field(OpenApiTypes.STR)
    def get_object_type(self, obj):
        """Return human-readable object type."""
        return f"{obj.content_type.app_label}.{obj.content_type.model}"

    @extend_schema_field(OpenApiTypes.STR)
    def get_object_repr(self, obj):
        """Return string representation of the referenced object."""
        try:
            return str(obj.content_object)
        except Exception:
            return f"{obj.content_type.model} #{obj.object_id}"
