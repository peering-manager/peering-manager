from django.shortcuts import get_object_or_404

from net.forms import ConnectionForm
from net.models import Connection
from utils.views import AddOrEditView, DeleteView, DetailsView, PermissionRequiredMixin


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
