from rest_framework import serializers

from extras.models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    JobResult,
    Webhook,
)
from peering_manager.api import WritableNestedSerializer
from users.api.nested_serializers import NestedUserSerializer


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


class NestedJobResultSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="extras-api:jobresult-detail")
    user = NestedUserSerializer(read_only=True)

    class Meta:
        model = JobResult
        fields = ["id", "url", "created", "completed", "user", "status"]


class NestedWebhookSerializer(WritableNestedSerializer):
    class Meta:
        model = Webhook
        fields = ["id", "name", "url"]
