from django.contrib.contenttypes.models import ContentType
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from extras.models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    JobResult,
    Webhook,
)
from peering_manager.api.fields import ContentTypeField
from peering_manager.api.serializers import ValidatedModelSerializer
from users.api.nested_serializers import NestedUserSerializer
from utils.api import get_serializer_for_model

from .nested_serializers import *

__all__ = (
    "ConfigContextSerializer",
    "ConfigContextAssignmentSerializer",
    "ExportTemplateSerializer",
    "JobResultSerializer",
    "WebhookSerializer",
    "NestedJobResultSerializer",
    "NestedWebhookSerializer",
)


class ConfigContextSerializer(ValidatedModelSerializer):
    class Meta:
        model = ConfigContext
        fields = [
            "id",
            "display",
            "name",
            "description",
            "is_active",
            "data",
        ]


class ConfigContextAssignmentSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="extras-api:configcontextassignment-detail"
    )
    content_type = ContentTypeField(queryset=ContentType.objects.all())
    object = serializers.SerializerMethodField(read_only=True)
    config_context = NestedConfigContextSerializer()

    class Meta:
        model = ConfigContextAssignment
        fields = [
            "id",
            "url",
            "display",
            "content_type",
            "object_id",
            "object",
            "config_context",
            "weight",
            "created",
            "updated",
        ]

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_object(self, instance):
        context = {"request": self.context["request"]}
        serializer = get_serializer_for_model(instance.object, prefix="Nested")
        return serializer(instance.object, context=context).data


class ExportTemplateSerializer(ValidatedModelSerializer):
    content_type = ContentTypeField(queryset=ContentType.objects.all())

    class Meta:
        model = ExportTemplate
        fields = [
            "id",
            "display",
            "name",
            "content_type",
            "description",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
        ]


class IXAPISerializer(ValidatedModelSerializer):
    class Meta:
        model = IXAPI
        fields = ["id", "display", "name", "url", "api_key", "api_secret", "identity"]


class IXAPIAccountSerializer(serializers.Serializer):
    url = serializers.CharField()
    api_key = serializers.CharField()
    api_secret = serializers.CharField()


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
