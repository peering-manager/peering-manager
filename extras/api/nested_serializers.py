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
    class Meta:
        model = ConfigContext
        fields = ["id", "url", "display_url", "display", "name"]


class NestedConfigContextAssignmentSerializer(WritableNestedSerializer):
    config_context = NestedConfigContextSerializer()

    class Meta:
        model = ConfigContextAssignment
        fields = ["id", "url", "display", "config_context"]


class NestedExportTemplateSerializer(WritableNestedSerializer):
    class Meta:
        model = ExportTemplate
        fields = ["id", "url", "display_url", "display", "name"]


class NestedIXAPISerializer(WritableNestedSerializer):
    class Meta:
        model = IXAPI
        fields = ["id", "url", "display_url", "display", "name"]


class NestedJournalEntrySerializer(WritableNestedSerializer):
    class Meta:
        model = JournalEntry
        fields = ["id", "url", "display_url", "display", "created"]


class NestedTagSerializer(WritableNestedSerializer):
    class Meta:
        model = Tag
        fields = ["id", "url", "display_url", "display", "name", "slug", "color"]


class NestedWebhookSerializer(WritableNestedSerializer):
    class Meta:
        model = Webhook
        fields = ["id", "url", "display_url", "display", "name"]
