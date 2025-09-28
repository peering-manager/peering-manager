from peering_manager.api.serializers import WritableNestedSerializer

from ..models import Contact, ContactAssignment, ContactRole, Email

__all__ = (
    "NestedContactAssignmentSerializer",
    "NestedContactRoleSerializer",
    "NestedContactSerializer",
    "NestedEmailSerializer",
)


class NestedContactRoleSerializer(WritableNestedSerializer):
    class Meta:
        model = ContactRole
        fields = ["id", "url", "display_url", "display", "name", "slug"]


class NestedContactSerializer(WritableNestedSerializer):
    class Meta:
        model = Contact
        fields = ["id", "url", "display_url", "display", "name"]


class NestedContactAssignmentSerializer(WritableNestedSerializer):
    contact = NestedContactSerializer()
    role = NestedContactRoleSerializer()

    class Meta:
        model = ContactAssignment
        fields = ["id", "url", "display", "contact", "role"]


class NestedEmailSerializer(WritableNestedSerializer):
    class Meta:
        model = Email
        fields = ["id", "url", "display_url", "display", "name"]
