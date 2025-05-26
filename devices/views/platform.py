from django.db.models import Count

from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
)
from utils.views import register_model_view

from ..filtersets import PlatformFilterSet
from ..forms import PlatformForm
from ..models import Platform
from ..tables import PlatformTable

__all__ = ("PlatformBulkDelete", "PlatformDelete", "PlatformEdit", "PlatformList")


@register_model_view(model=Platform, name="list", path="", detail=False)
class PlatformList(ObjectListView):
    permission_required = "devices.view_platform"
    queryset = Platform.objects.annotate(
        router_count=Count("router", distinct=True)
    ).order_by("name")
    table = PlatformTable
    template_name = "devices/platform/list.html"


@register_model_view(model=Platform, name="add", detail=False)
@register_model_view(model=Platform, name="edit")
class PlatformEdit(ObjectEditView):
    queryset = Platform.objects.all()
    form = PlatformForm


@register_model_view(model=Platform, name="delete")
class PlatformDelete(ObjectDeleteView):
    permission_required = "devices.delete_platform"
    queryset = Platform.objects.all()


@register_model_view(model=Platform, name="bulk_delete", path="delete", detail=False)
class PlatformBulkDelete(BulkDeleteView):
    queryset = Platform.objects.all()
    filterset = PlatformFilterSet
    table = PlatformTable
