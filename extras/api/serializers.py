from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
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
    TableConfig,
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
    "TableConfigSerializer",
    "TagSerializer",
    "WebhookSerializer",
)


class ConfigContextSerializer(ValidatedModelSerializer):
    class Meta:
        model = ConfigContext
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "description",
            "is_active",
            "data",
            "data_source",
            "data_file",
            "data_path",
            "data_synchronised",
            "auto_synchronisation_enabled",
        ]


class ConfigContextAssignmentSerializer(ValidatedModelSerializer):
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
            "display_url",
            "url",
            "name",
            "content_type",
            "description",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
            "data_source",
            "data_file",
            "data_path",
            "data_synchronised",
            "auto_synchronisation_enabled",
        ]


class TableConfigSerializer(ValidatedModelSerializer):
    object_type = ContentTypeField(queryset=ContentType.objects.all(), required=False, allow_null=True)

    class Meta:
        model = TableConfig
        fields = [
            "id",
            "display",
            "display_url",
            "url",
            "table",
            "object_type",
            "columns",
            "created",
            "updated",
        ]


class IXAPISerializer(ValidatedModelSerializer):
    api_secret = serializers.CharField(write_only=True)

    class Meta:
        model = IXAPI
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "api_url",
            "api_key",
            "api_secret",
            "identity",
        ]


class IXAPIAccountSerializer(serializers.Serializer):
    """
    Details used to list the accounts of an IX-API that is not recorded yet.

    An existing IX-API can be referenced instead of, or together with, the connection
    details. The details that the caller omits are then read from that object, so the
    key and the secret of a known IX-API never have to leave the server.
    """

    ixapi = serializers.PrimaryKeyRelatedField(queryset=IXAPI.objects.all(), required=False, allow_null=True)
    api_url = serializers.CharField(required=False, allow_blank=True)
    api_key = serializers.CharField(required=False, allow_blank=True)
    api_secret = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        known = data.get("ixapi")
        for field in ("api_url", "api_key", "api_secret"):
            if not data.get(field):
                data[field] = getattr(known, field, "")
            if not data[field]:
                raise serializers.ValidationError({field: "This field is required unless an existing IX-API is given."})

        # The server connects to this URL, so only absolute HTTP URLs are accepted
        try:
            URLValidator(schemes=["http", "https"])(data["api_url"])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"api_url": "Enter a valid HTTP or HTTPS URL."}) from e

        return data


class JournalEntrySerializer(PeeringManagerModelSerializer):
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
            "display_url",
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
                data["assigned_object_type"].get_object_for_this_type(id=data["assigned_object_id"])
            except ObjectDoesNotExist:
                raise serializers.ValidationError(
                    f"Invalid assigned_object: {data['assigned_object_type']} ID {data['assigned_object_id']}"
                ) from None

        return super().validate(data)

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_assigned_object(self, instance):
        serializer = get_serializer_for_model(instance.assigned_object_type.model_class(), prefix="Nested")
        return serializer(
            instance.assigned_object,
            context={"request": self.context["request"]},
        ).data


class TagSerializer(ValidatedModelSerializer):
    tagged_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "slug",
            "color",
            "description",
            "tagged_items",
        ]


class WebhookSerializer(ValidatedModelSerializer):
    content_types = ContentTypeField(
        queryset=ContentType.objects.filter(FeatureQuery("webhooks").get_query()),
        many=True,
    )

    class Meta:
        model = Webhook
        fields = [
            "id",
            "url",
            "display_url",
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
