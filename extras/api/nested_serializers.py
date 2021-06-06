from rest_framework import serializers

from extras.models import JobResult, Webhook
from users.api.nested_serializers import UserNestedSerializer
from utils.api import WritableNestedSerializer


class JobResultNestedSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="extras-api:jobresult-detail")
    user = UserNestedSerializer(read_only=True)

    class Meta:
        model = JobResult
        fields = ["url", "created", "completed", "user", "status"]


class WebhookNestedSerializer(WritableNestedSerializer):
    class Meta:
        model = Webhook
        fields = ["id", "name", "url"]
