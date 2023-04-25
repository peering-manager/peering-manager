from rest_framework import serializers

from messaging.models import Contact, ContactAssignment, ContactRole, Email
from peering_manager.api.serializers import WritableNestedSerializer


class NestedContactRoleSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="messaging-api:contactrole-detail"
    )

    class Meta:
        model = ContactRole
        fields = ["id", "url", "display", "name", "slug"]


class NestedContactSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="messaging-api:contact-detail")

    class Meta:
        model = Contact
        fields = ["id", "url", "display", "name"]


class NestedContactAssignmentSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="messaging-api:contactassignment-detail"
    )
    contact = NestedContactSerializer()
    role = NestedContactRoleSerializer()

    class Meta:
        model = ContactAssignment
        fields = ["id", "url", "display", "contact", "role"]


class NestedEmailSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="messaging-api:email-detail")

    class Meta:
        model = Email
        fields = ["id", "url", "display", "name"]
