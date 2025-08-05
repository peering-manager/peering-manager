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

from ..filtersets import DirectPeeringSessionFilterSet
from ..forms import (
    DirectPeeringSessionBulkEditForm,
    DirectPeeringSessionFilterForm,
    DirectPeeringSessionForm,
)
from ..models import DirectPeeringSession
from ..tables import DirectPeeringSessionTable

__all__ = (
    "DirectPeeringSessionBulkDelete",
    "DirectPeeringSessionBulkEdit",
    "DirectPeeringSessionConfigContext",
    "DirectPeeringSessionDelete",
    "DirectPeeringSessionEdit",
    "DirectPeeringSessionList",
    "DirectPeeringSessionView",
)


@register_model_view(DirectPeeringSession, name="list", path="", detail=False)
class DirectPeeringSessionList(ObjectListView):
    permission_required = "peering.view_directpeeringsession"
    queryset = (
        DirectPeeringSession.objects.order_by(
            "local_autonomous_system", "autonomous_system", "ip_address"
        )
        .select_related("local_autonomous_system", "autonomous_system")
        .defer(
            "local_autonomous_system__prefixes",
            "autonomous_system__prefixes",
            "local_autonomous_system__as_list",
            "autonomous_system__as_list",
        )
    )
    table = DirectPeeringSessionTable
    filterset = DirectPeeringSessionFilterSet
    filterset_form = DirectPeeringSessionFilterForm
    template_name = "peering/directpeeringsession/list.html"


@register_model_view(DirectPeeringSession)
class DirectPeeringSessionView(ObjectView):
    permission_required = "peering.view_directpeeringsession"
    queryset = DirectPeeringSession.objects.all()


@register_model_view(model=DirectPeeringSession, name="add", detail=False)
@register_model_view(model=DirectPeeringSession, name="edit")
class DirectPeeringSessionEdit(ObjectEditView):
    queryset = DirectPeeringSession.objects.all()
    form = DirectPeeringSessionForm


@register_model_view(DirectPeeringSession, name="delete")
class DirectPeeringSessionDelete(ObjectDeleteView):
    permission_required = "peering.delete_directpeeringsession"
    queryset = DirectPeeringSession.objects.all()


@register_model_view(DirectPeeringSession, name="bulk_edit", path="edit", detail=False)
class DirectPeeringSessionBulkEdit(BulkEditView):
    permission_required = "peering.change_directpeeringsession"
    queryset = DirectPeeringSession.objects.select_related("autonomous_system").defer(
        "autonomous_system__prefixes", "autonomous_system__as_list"
    )
    filterset = DirectPeeringSessionFilterSet
    table = DirectPeeringSessionTable
    form = DirectPeeringSessionBulkEditForm


@register_model_view(
    DirectPeeringSession, name="bulk_delete", path="delete", detail=False
)
class DirectPeeringSessionBulkDelete(BulkDeleteView):
    queryset = DirectPeeringSession.objects.all()
    filterset = DirectPeeringSessionFilterSet
    table = DirectPeeringSessionTable


@register_model_view(DirectPeeringSession, name="configcontext", path="config-context")
class DirectPeeringSessionConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_directpeeringsession"
    queryset = DirectPeeringSession.objects.all()
    base_template = "peering/directpeeringsession/_base.html"
