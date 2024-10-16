from django.contrib.contenttypes.models import ContentType
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from extras.utils import FeatureQuery
from peering_manager.api.fields import ContentTypeField
from peering_manager.api.serializers import ValidatedModelSerializer
from utils.api import get_serializer_for_model

from ..models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    Tag,
    Webhook,
)
from .nested_serializers import *

__all__ = (
    "ConfigContextSerializer",
    "ConfigContextAssignmentSerializer",
    "ExportTemplateSerializer",
    "TagSerializer",
    "WebhookSerializer",
    "NestedTagSerializer",
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


class TagSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="extras-api:tag-detail")
    tagged_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = [
            "id",
            "url",
            "display",
            "name",
            "slug",
            "color",
            "description",
            "tagged_items",
        ]


class WebhookSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="extras-api:webhook-detail")
    content_types = ContentTypeField(
        queryset=ContentType.objects.filter(FeatureQuery("webhooks").get_query()),
        many=True,
    )

    class Meta:
        model = Webhook
        fields = [
            "id",
            "url",
            "display",
            "content_types",
            "name",
            "type_create",
            "type_update",
            "type_delete",
            "payload_url",
            "enabled",
            "http_method",
            "http_content_type",
            "additional_headers",
            "body_template",
            "secret",
            "conditions",
            "ssl_verification",
            "ca_file_path",
            "created",
            "updated",
        ]
