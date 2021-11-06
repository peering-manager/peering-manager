from rest_framework import serializers

from extras.models import IXAPI, JobResult, Webhook
from peering_manager.api.fields import ContentTypeField
from peering_manager.api.serializers import BaseModelSerializer
from users.api.nested_serializers import NestedUserSerializer

from .nested_serializers import *

__all__ = (
    "JobResultSerializer",
    "WebhookSerializer",
    "NestedJobResultSerializer",
    "NestedWebhookSerializer",
)


class IXAPISerializer(BaseModelSerializer):
    class Meta:
        model = IXAPI
        fields = ["id", "display", "name", "url", "api_key", "api_secret", "identity"]


class JobResultSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="extras-api:jobresult-detail")
    user = NestedUserSerializer(read_only=True)
    obj_type = ContentTypeField(read_only=True)
    output = serializers.CharField(read_only=True)

    class Meta:
        model = JobResult
        fields = [
            "id",
            "url",
            "created",
            "completed",
            "name",
            "obj_type",
            "status",
            "user",
            "data",
            "job_id",
            "output",
        ]


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = [
            "id",
            "name",
            "type_create",
            "type_update",
            "type_delete",
            "url",
            "enabled",
            "http_method",
            "http_content_type",
            "secret",
            "ssl_verification",
            "ca_file_path",
        ]
