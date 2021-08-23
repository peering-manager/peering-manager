from rest_framework.routers import APIRootView

from extras.filters import JobResultFilterSet, WebhookFilterSet
from extras.models import IXAPI, JobResult, Webhook
from peering_manager.api.views import ModelViewSet, ReadOnlyModelViewSet

from .serializers import IXAPISerializer, JobResultSerializer, WebhookSerializer


class ExtrasRootView(APIRootView):
    def get_view_name(self):
        return "Extras"


class IXAPIViewSet(ModelViewSet):
    queryset = IXAPI.objects.all()
    serializer_class = IXAPISerializer


class JobResultViewSet(ReadOnlyModelViewSet):
    queryset = JobResult.objects.all()
    serializer_class = JobResultSerializer
    filterset_class = JobResultFilterSet


class WebhookViewSet(ModelViewSet):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    filterset_class = WebhookFilterSet
