from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema_field

from messaging.models import Contact, ContactAssignment, ContactRole, Email
from peering_manager.api.fields import ContentTypeField
from peering_manager.api.serializers import PeeringManagerModelSerializer

from .nested_serializers import *

__all__ = (
    "ContactSerializer",
    "NestedContactSerializer",
    "ContactRoleSerializer",
    "NestedContactRoleSerializer",
    "ContactAssignmentSerializer",
    "NestedContactAssignmentSerializer",
    "EmailSerializer",
    "NestedEmailSerializer",
)


class ContactRoleSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = ContactRole
        fields = ["id", "display", "name", "slug", "description", "tags"]


class ContactSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "display",
            "name",
            "title",
            "phone",
            "email",
            "address",
            "comments",
            "created",
            "updated",
        ]


class ContactAssignmentSerializer(PeeringManagerModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="messaging-api:contactassignment-detail"
    )
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
            "display",
            "name",
            "subject",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
            "comments",
            "tags",
        ]
