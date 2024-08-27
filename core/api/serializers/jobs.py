from rest_framework import serializers

from peering_manager.api.fields import ChoiceField, ContentTypeField
from peering_manager.api.serializers import BaseModelSerializer
from users.api.nested_serializers import NestedUserSerializer

from ...enums import *
from ...models import *

__all__ = ("JobSerializer", "NestedJobSerializer")


class JobSerializer(BaseModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core-api:job-detail")
    user = NestedUserSerializer(read_only=True)
    status = ChoiceField(choices=JobStatus, read_only=True)
    object_type = ContentTypeField(read_only=True)
    output = serializers.CharField(read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "url",
            "display",
            "object_type",
            "object_id",
            "name",
            "status",
            "created",
            "started",
            "completed",
            "user",
            "data",
            "job_id",
            "output",
        ]


class NestedJobSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core-api:job-detail")
    status = ChoiceField(choices=JobStatus)
    user = NestedUserSerializer(read_only=True)

    class Meta:
        model = Job
        fields = ["url", "created", "completed", "user", "status"]
