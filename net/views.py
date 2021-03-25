from net.forms import ConnectionForm
from net.models import Connection
from utils.views import AddOrEditView, PermissionRequiredMixin


class ConnectionAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "net.add_connection"
    model = Connection
    form = ConnectionForm
    template = "net/connection/add_edit.html"
