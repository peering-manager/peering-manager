from extras.views import ObjectConfigContextView
from net.filters import ConnectionFilterSet
from net.forms import ConnectionBulkEditForm, ConnectionFilterForm, ConnectionForm
from net.models import Connection
from net.tables import ConnectionTable
from peering_manager.views.generics import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
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

    def get_extra_context(self, request, instance):
        return {"active_tab": "main"}


class ConnectionContext(ObjectConfigContextView):
    permission_required = "net.view_connection"
    queryset = Connection.objects.all()
    base_template = "net/connection/_base.html"


class ConnectionAdd(ObjectEditView):
    permission_required = "net.add_connection"
    queryset = Connection.objects.all()
    model_form = ConnectionForm
    template_name = "net/connection/add_edit.html"


class ConnectionEdit(ObjectEditView):
    permission_required = "net.change_connection"
    queryset = Connection.objects.all()
    model_form = ConnectionForm
    template_name = "net/connection/add_edit.html"


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
    permission_required = "net.delete_connection"
    queryset = Connection.objects.all()
    filterset = ConnectionFilterSet
    table = ConnectionTable
