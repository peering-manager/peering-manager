from rest_framework import serializers

from extras.models import JobResult, Webhook
from peering_manager.api.serializers import WritableNestedSerializer
from users.api.nested_serializers import NestedUserSerializer


class NestedJobResultSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="extras-api:jobresult-detail")
    user = NestedUserSerializer(read_only=True)

    class Meta:
        model = JobResult
        fields = ["url", "created", "completed", "user", "status"]


class NestedWebhookSerializer(WritableNestedSerializer):
    class Meta:
        model = Webhook
        fields = ["id", "name", "url"]
