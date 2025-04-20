from extras.views import ObjectConfigContextView
from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import ConnectionFilterSet
from ..forms import ConnectionBulkEditForm, ConnectionFilterForm, ConnectionForm
from ..models import Connection
from ..tables import ConnectionTable

__all__ = (
    "ConnectionBulkDelete",
    "ConnectionBulkEdit",
    "ConnectionConfigContext",
    "ConnectionDelete",
    "ConnectionEdit",
    "ConnectionList",
    "ConnectionView",
)


@register_model_view(model=Connection, name="list", path="", detail=False)
class ConnectionList(ObjectListView):
    permission_required = "net.view_connection"
    queryset = Connection.objects.prefetch_related("internet_exchange_point", "router")
    filterset = ConnectionFilterSet
    filterset_form = ConnectionFilterForm
    table = ConnectionTable
    template_name = "net/connection/list.html"


@register_model_view(model=Connection)
class ConnectionView(ObjectView):
    permission_required = "net.view_connection"
    queryset = Connection.objects.all()

    def get_extra_context(self, request, instance):
        ixapi_network_service_config = instance.ixapi_network_service_config()
        return {
            "ixapi_network_service_config": ixapi_network_service_config,
            "ixapi_mac_address": instance.ixapi_mac_address(
                ixapi_network_service_config
            ),
        }


@register_model_view(model=Connection, name="add", detail=False)
@register_model_view(model=Connection, name="edit")
class ConnectionEdit(ObjectEditView):
    queryset = Connection.objects.all()
    form = ConnectionForm


@register_model_view(model=Connection, name="delete")
class ConnectionDelete(ObjectDeleteView):
    permission_required = "net.delete_connection"
    queryset = Connection.objects.all()


@register_model_view(model=Connection, name="bulk_edit", path="edit", detail=False)
class ConnectionBulkEdit(BulkEditView):
    permission_required = "net.change_connection"
    queryset = Connection.objects.select_related("internet_exchange_point", "router")
    filterset = ConnectionFilterSet
    table = ConnectionTable
    form = ConnectionBulkEditForm


@register_model_view(model=Connection, name="bulk_delete", path="delete", detail=False)
class ConnectionBulkDelete(BulkDeleteView):
    queryset = Connection.objects.all()
    filterset = ConnectionFilterSet
    table = ConnectionTable


@register_model_view(model=Connection, name="configcontext", path="config-context")
class ConnectionConfigContext(ObjectConfigContextView):
    permission_required = "net.view_connection"
    queryset = Connection.objects.all()
    base_template = "net/connection/_base.html"
