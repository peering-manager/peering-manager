from rest_framework import serializers

from peering_manager.api.serializers import WritableNestedSerializer

from ..models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    JournalEntry,
    Tag,
    Webhook,
)


class NestedConfigContextSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="extras-api:configcontext-detail"
    )

    class Meta:
        model = ConfigContext
        fields = ["id", "url", "display", "name"]


class NestedConfigContextAssignmentSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="extras-api:configcontextassignment-detail"
    )
    config_context = NestedConfigContextSerializer()

    class Meta:
        model = ConfigContextAssignment
        fields = ["id", "url", "display", "config_context"]


class NestedExportTemplateSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="extras-api:exporttemplate-detail"
    )

    class Meta:
        model = ExportTemplate
        fields = ["id", "url", "display", "name"]


class NestedIXAPISerializer(WritableNestedSerializer):
    class Meta:
        model = IXAPI
        fields = ["id", "display", "name", "url"]


class NestedJournalEntrySerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="extras-api:journalentry-detail"
    )

    class Meta:
        model = JournalEntry
        fields = ["id", "url", "display", "created"]


class NestedTagSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="extras-api:tag-detail")

    class Meta:
        model = Tag
        fields = ["id", "url", "name", "slug", "color"]


class NestedWebhookSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="extras-api:webhook-detail")

    class Meta:
        model = Webhook
        fields = ["id", "name", "url"]
