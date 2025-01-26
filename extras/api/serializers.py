from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from peering_manager.api.fields import ChoiceField, ContentTypeField
from peering_manager.api.serializers import (
    PeeringManagerModelSerializer,
    ValidatedModelSerializer,
)
from utils.api import get_serializer_for_model

from ..enums import JournalEntryKind
from ..models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    JournalEntry,
    Tag,
    Webhook,
)
from ..utils import FeatureQuery
from .nested_serializers import *

__all__ = (
    "ConfigContextAssignmentSerializer",
    "ConfigContextSerializer",
    "ExportTemplateSerializer",
    "JournalEntrySerializer",
    "NestedJournalEntrySerializer",
    "NestedTagSerializer",
    "NestedWebhookSerializer",
    "TagSerializer",
    "WebhookSerializer",
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


class JournalEntrySerializer(PeeringManagerModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="extras-api:journalentry-detail"
    )
    assigned_object_type = ContentTypeField(queryset=ContentType.objects.all())
    assigned_object = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        queryset=User.objects.all(),
        required=False,
        default=serializers.CurrentUserDefault(),
    )
    kind = ChoiceField(choices=JournalEntryKind, required=False)

    class Meta:
        model = JournalEntry
        fields = [
            "id",
            "url",
            "display",
            "assigned_object_type",
            "assigned_object_id",
            "assigned_object",
            "created",
            "updated",
            "created_by",
            "kind",
            "comments",
            "tags",
        ]

    def validate(self, data):
        # Validate that the parent object exists
        if "assigned_object_type" in data and "assigned_object_id" in data:
            try:
                data["assigned_object_type"].get_object_for_this_type(
                    id=data["assigned_object_id"]
                )
            except ObjectDoesNotExist:
                raise serializers.ValidationError(
                    f"Invalid assigned_object: {data['assigned_object_type']} ID {data['assigned_object_id']}"
                ) from None

        return super().validate(data)

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_assigned_object(self, instance):
        serializer = get_serializer_for_model(
            instance.assigned_object_type.model_class(), prefix="Nested"
        )
        return serializer(
            instance.assigned_object,
            context={"request": self.context["request"]},
        ).data


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
