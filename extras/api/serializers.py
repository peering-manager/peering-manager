from django.contrib.contenttypes.models import ContentType
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from extras.enums import ObjectChangeAction
from extras.models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    ObjectChange,
    Tag,
    Webhook,
)
from peering_manager.api.fields import ChoiceField, ContentTypeField
from peering_manager.api.serializers import (
    BaseModelSerializer,
    ValidatedModelSerializer,
)
from users.api.nested_serializers import NestedUserSerializer
from utils.api import get_serializer_for_model

from .nested_serializers import *

__all__ = (
    "ConfigContextSerializer",
    "ConfigContextAssignmentSerializer",
    "ExportTemplateSerializer",
    "ObjectChangeSerializer",
    "TagSerializer",
    "WebhookSerializer",
    "NestedConfigContextSerializer",
    "NestedConfigContextAssignmentSerializer",
    "NestedExportTemplateSerializer",
    "NestedIXAPISerializer",
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


class ObjectChangeSerializer(BaseModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="extras-api:objectchange-detail"
    )
    user = NestedUserSerializer(read_only=True)
    action = ChoiceField(choices=ObjectChangeAction, read_only=True)
    changed_object_type = ContentTypeField(read_only=True)
    changed_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ObjectChange
        fields = [
            "id",
            "url",
            "display",
            "time",
            "user",
            "user_name",
            "request_id",
            "action",
            "changed_object_type",
            "changed_object_id",
            "changed_object",
            "prechange_data",
            "postchange_data",
        ]

    @extend_schema_field(serializers.DictField)
    def get_changed_object(self, o):
        """
        Serialize a nested representation of the changed object.
        """
        if o.changed_object is None:
            return None

        try:
            serializer = get_serializer_for_model(o.changed_object, prefix="Nested")
        except Exception:
            return o.object_repr

        context = {"request": self.context["request"]}
        data = serializer(o.changed_object, context=context).data

        return data


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
            "comments",
            "tagged_items",
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
