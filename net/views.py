from django.shortcuts import get_object_or_404

from net.filters import ConnectionFilterSet
from net.forms import ConnectionBulkEditForm, ConnectionFilterForm, ConnectionForm
from net.models import Connection
from net.tables import ConnectionTable
from utils.views import (
    AddOrEditView,
    BulkDeleteView,
    BulkEditView,
    DeleteView,
    DetailsView,
    ModelListView,
    PermissionRequiredMixin,
)


class ConnectionList(PermissionRequiredMixin, ModelListView):
    permission_required = "net.view_connection"
    queryset = Connection.objects.prefetch_related("internet_exchange_point", "router")
    filter = ConnectionFilterSet
    filter_form = ConnectionFilterForm
    table = ConnectionTable
    template = "net/connection/list.html"


class ConnectionAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "net.add_connection"
    model = Connection
    form = ConnectionForm
    template = "net/connection/add_edit.html"


class ConnectionDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "net.delete_connection"
    model = Connection
    return_url = "net:connection_list"


class ConnectionDetails(DetailsView):
    permission_required = "net.view_connection"
    queryset = Connection.objects.all()

    def get_context(self, request, **kwargs):
        return {
            "instance": get_object_or_404(self.queryset, **kwargs),
            "active_tab": "main",
        }


class ConnectionEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "net.change_connection"
    model = Connection
    form = ConnectionForm
    template = "net/connection/add_edit.html"


class ConnectionBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "net.change_connection"
    queryset = Connection.objects.select_related("internet_exchange_point", "router")
    filter = ConnectionFilterSet
    table = ConnectionTable
    form = ConnectionBulkEditForm


class ConnectionBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "net.delete_connection"
    model = Connection
    filter = ConnectionFilterSet
    table = ConnectionTable
