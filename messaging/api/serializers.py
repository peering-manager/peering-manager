from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from peering_manager.api.fields import ContentTypeField
from peering_manager.api.serializers import PeeringManagerModelSerializer

from ..models import Contact, ContactAssignment, ContactRole, Email
from .nested_serializers import *

__all__ = (
    "ContactAssignmentSerializer",
    "ContactRoleSerializer",
    "ContactSerializer",
    "EmailSendingSerializer",
    "EmailSerializer",
)


class ContactRoleSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = ContactRole
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "slug",
            "description",
            "tags",
            "created",
            "updated",
        ]


class ContactSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "title",
            "phone",
            "email",
            "address",
            "description",
            "comments",
            "tags",
            "created",
            "updated",
        ]


class ContactAssignmentSerializer(PeeringManagerModelSerializer):
    content_type = ContentTypeField(queryset=ContentType.objects.all())
    object = serializers.SerializerMethodField(read_only=True)
    contact = NestedContactSerializer()
    role = NestedContactRoleSerializer(required=False, allow_null=True)

    class Meta:
        model = ContactAssignment
        fields = [
            "id",
            "url",
            "display",
            "content_type",
            "object_id",
            "object",
            "contact",
            "role",
            "created",
            "updated",
        ]

    @extend_schema_field(NestedContactSerializer)
    def get_object(self, instance):
        context = {"request": self.context["request"]}
        return NestedContactSerializer(instance.object, context=context).data


class EmailSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = Email
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "subject",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
            "comments",
            "tags",
            "created",
            "updated",
        ]


class EmailSendingSerializer(serializers.Serializer):
    email = serializers.IntegerField()
    autonomous_system = serializers.IntegerField(required=False)
    network = serializers.IntegerField(required=False)
