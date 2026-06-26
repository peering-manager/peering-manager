from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import TableConfigFilterSet
from ..forms import TableConfigFilterForm
from ..models import TableConfig
from ..tables import TableConfigTable

__all__ = (
    "TableConfigBulkDeleteView",
    "TableConfigDeleteView",
    "TableConfigListView",
    "TableConfigView",
)


@register_model_view(TableConfig, name="list", path="", detail=False)
class TableConfigListView(ObjectListView):
    permission_required = "extras.view_tableconfig"
    queryset = TableConfig.objects.all()
    filterset = TableConfigFilterSet
    filterset_form = TableConfigFilterForm
    table = TableConfigTable
    template_name = "extras/tableconfig/list.html"


@register_model_view(TableConfig)
class TableConfigView(ObjectView):
    permission_required = "extras.view_tableconfig"
    queryset = TableConfig.objects.all()


@register_model_view(TableConfig, name="delete")
class TableConfigDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_tableconfig"
    queryset = TableConfig.objects.all()


@register_model_view(TableConfig, name="bulk_delete", detail=False)
class TableConfigBulkDeleteView(BulkDeleteView):
    permission_required = "extras.delete_tableconfig"
    queryset = TableConfig.objects.all()
    filterset = TableConfigFilterSet
    table = TableConfigTable
