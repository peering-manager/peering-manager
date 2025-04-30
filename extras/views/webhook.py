from peering_manager.views.generic import (
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import WebhookFilterSet
from ..forms import WebhookFilterForm, WebhookForm
from ..models import Webhook
from ..tables import WebhookTable

__all__ = ("WebhookDelete", "WebhookEdit", "WebhookList", "WebhookView")


@register_model_view(Webhook, name="list", path="", detail=False)
class WebhookList(ObjectListView):
    permission_required = "extras.view_webhook"
    queryset = Webhook.objects.all()
    filterset = WebhookFilterSet
    filterset_form = WebhookFilterForm
    table = WebhookTable
    template_name = "extras/webhook/list.html"


@register_model_view(Webhook)
class WebhookView(ObjectView):
    permission_required = "extras.view_webhook"
    queryset = Webhook.objects.all()


@register_model_view(model=Webhook, name="add", detail=False)
@register_model_view(model=Webhook, name="edit")
class WebhookEdit(ObjectEditView):
    queryset = Webhook.objects.all()
    form = WebhookForm


@register_model_view(model=Webhook, name="delete")
class WebhookDelete(ObjectDeleteView):
    permission_required = "extras.delete_webhook"
    queryset = Webhook.objects.all()
