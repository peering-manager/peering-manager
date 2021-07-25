from django.contrib.auth.models import Group, User
from rest_framework import serializers

from .nested_serializers import *

__all__ = (
    "GroupSerializer",
    "UserSerializer",
    "NestedGroupSerializer",
    "NestedUserSerializer",
)


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="users-api:user-detail")
    groups = NestedGroupSerializer(many=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "url",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_active",
            "date_joined",
            "groups",
        ]


class GroupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="users-api:group-detail")
    user_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = ["id", "url", "name", "user_count"]
