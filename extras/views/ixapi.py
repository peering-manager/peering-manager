import logging

from django.contrib import messages

from peering.models import InternetExchange
from peering_manager.views.generic import (
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import IXAPIFilterSet
from ..forms import IXAPIFilterForm, IXAPIForm
from ..models import IXAPI
from ..tables import IXAPITable

__all__ = ("IXAPIDeleteView", "IXAPIEditView", "IXAPIListView", "IXAPIView")

logger = logging.getLogger("peering.manager.extras.ixapi")


@register_model_view(IXAPI, name="list", path="", detail=False)
class IXAPIListView(ObjectListView):
    permission_required = "extras.view_ixapi"
    queryset = IXAPI.objects.all()
    filterset = IXAPIFilterSet
    filterset_form = IXAPIFilterForm
    table = IXAPITable
    template_name = "extras/ixapi/list.html"


@register_model_view(IXAPI)
class IXAPIView(ObjectView):
    permission_required = "extras.view_ixapi"
    queryset = IXAPI.objects.all()

    def get_extra_context(self, request, instance):
        context = {
            "internet_exchange_points": InternetExchange.objects.filter(ixapi_endpoint=instance),
            "version": None,
            "identity": None,
        }

        try:
            context["version"] = instance.version
            context["identity"] = instance.get_identity()
        except Exception as e:
            logger.error(f"cannot query ix-api {instance} (pk: {instance.pk}): {e}")
            messages.error(request, f"Unable to fetch data from {instance}, check its URL, key and secret: {e}")

        return context


@register_model_view(model=IXAPI, name="add", detail=False)
@register_model_view(model=IXAPI, name="edit")
class IXAPIEditView(ObjectEditView):
    queryset = IXAPI.objects.all()
    form = IXAPIForm
    template_name = "extras/ixapi/edit.html"


@register_model_view(IXAPI, name="delete")
class IXAPIDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_ixapi"
    queryset = IXAPI.objects.all()
