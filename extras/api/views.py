from extras.filters import JobResultFilterSet, WebhookFilterSet
from extras.models import JobResult, Webhook
from peering_manager.api.views import (
    ModelViewSet,
    ReadOnlyModelViewSet,
    StaticChoicesViewSet,
)

from .serializers import JobResultSerializer, WebhookSerializer


class ExtrasFieldChoicesViewSet(StaticChoicesViewSet):
    fields = [(JobResult, ["status"])]


class JobResultViewSet(ReadOnlyModelViewSet):
    queryset = JobResult.objects.all()
    serializer_class = JobResultSerializer
    filterset_class = JobResultFilterSet


class WebhookViewSet(ModelViewSet):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    filterset_class = WebhookFilterSet
