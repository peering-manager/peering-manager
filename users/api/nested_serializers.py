from django.contrib.auth.models import Group, User
from rest_framework import serializers

from utils.api import WriteEnabledNestedSerializer


class GroupNestedSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="users-api:group-detail")

    class Meta:
        model = Group
        fields = ["id", "url", "name"]


class UserNestedSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="users-api:user-detail")

    class Meta:
        model = User
        fields = ["id", "url", "username"]
