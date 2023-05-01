from rest_framework import serializers

from extras.models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    Webhook,
)
from peering_manager.api.serializers import WritableNestedSerializer


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


class NestedWebhookSerializer(WritableNestedSerializer):
    class Meta:
        model = Webhook
        fields = ["id", "name", "url"]
