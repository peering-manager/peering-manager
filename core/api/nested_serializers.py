from rest_framework import serializers

from peering_manager.api.fields import ChoiceField
from users.api.nested_serializers import NestedUserSerializer

from ..enums import JobStatus
from ..models import *

__all__ = ("NestedJobSerializer",)


class NestedJobSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core-api:job-detail")
    status = ChoiceField(choices=JobStatus)
    user = NestedUserSerializer(read_only=True)

    class Meta:
        model = Job
        fields = ["url", "created", "completed", "user", "status"]
