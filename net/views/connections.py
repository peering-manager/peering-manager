from extras.views import ObjectConfigContextView
from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)

from ..filtersets import ConnectionFilterSet
from ..forms import ConnectionBulkEditForm, ConnectionFilterForm, ConnectionForm
from ..models import Connection
from ..tables import ConnectionTable

__all__ = (
    "ConnectionList",
    "ConnectionView",
    "ConnectionContext",
    "ConnectionEdit",
    "ConnectionBulkEdit",
    "ConnectionDelete",
    "ConnectionBulkDelete",
)


class ConnectionList(ObjectListView):
    permission_required = "net.view_connection"
    queryset = Connection.objects.prefetch_related("internet_exchange_point", "router")
    filterset = ConnectionFilterSet
    filterset_form = ConnectionFilterForm
    table = ConnectionTable
    template_name = "net/connection/list.html"


class ConnectionView(ObjectView):
    permission_required = "net.view_connection"
    queryset = Connection.objects.all()
    tab = "main"

    def get_extra_context(self, request, instance):
        ixapi_network_service_config = instance.ixapi_network_service_config()
        return {
            "ixapi_network_service_config": ixapi_network_service_config,
            "ixapi_mac_address": instance.ixapi_mac_address(
                ixapi_network_service_config
            ),
        }


class ConnectionContext(ObjectConfigContextView):
    permission_required = "net.view_connection"
    queryset = Connection.objects.all()
    base_template = "net/connection/_base.html"


class ConnectionEdit(ObjectEditView):
    queryset = Connection.objects.all()
    form = ConnectionForm


class ConnectionBulkEdit(BulkEditView):
    permission_required = "net.change_connection"
    queryset = Connection.objects.select_related("internet_exchange_point", "router")
    filterset = ConnectionFilterSet
    table = ConnectionTable
    form = ConnectionBulkEditForm


class ConnectionDelete(ObjectDeleteView):
    permission_required = "net.delete_connection"
    queryset = Connection.objects.all()


class ConnectionBulkDelete(BulkDeleteView):
    queryset = Connection.objects.all()
    filterset = ConnectionFilterSet
    table = ConnectionTable
