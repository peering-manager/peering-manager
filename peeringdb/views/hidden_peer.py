from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import HiddenPeerFilterSet
from ..forms import HiddenPeerFilterForm, HidePeerForm
from ..models import HiddenPeer
from ..tables import HiddenPeerTable

__all__ = (
    "HiddenPeerBulkDelete",
    "HiddenPeerDeleteView",
    "HiddenPeerEditView",
    "HiddenPeerList",
    "HiddenPeerView",
)


@register_model_view(HiddenPeer, name="list", path="", detail=False)
class HiddenPeerList(ObjectListView):
    permission_required = "peeringdb.view_hiddenpeer"
    queryset = HiddenPeer.objects.all()
    filterset = HiddenPeerFilterSet
    filterset_form = HiddenPeerFilterForm
    table = HiddenPeerTable
    template_name = "peeringdb/hiddenpeer/list.html"


@register_model_view(HiddenPeer)
class HiddenPeerView(ObjectView):
    permission_required = "peeringdb.view_hiddenpeer"
    queryset = HiddenPeer.objects.all()


@register_model_view(model=HiddenPeer, name="add", detail=False)
@register_model_view(model=HiddenPeer, name="edit")
class HiddenPeerEditView(ObjectEditView):
    permission_required = "peeringdb.change_hiddenpeer"
    queryset = HiddenPeer.objects.all()
    form = HidePeerForm
    template_name = "peeringdb/hiddenpeer/edit.html"


@register_model_view(model=HiddenPeer, name="delete")
class HiddenPeerDeleteView(ObjectDeleteView):
    permission_required = "peeringdb.delete_hiddenpeer"
    queryset = HiddenPeer.objects.all()


@register_model_view(HiddenPeer, name="bulk_delete", path="delete", detail=False)
class HiddenPeerBulkDelete(BulkDeleteView):
    queryset = HiddenPeer.objects.all()
    filterset = HiddenPeerFilterSet
    table = HiddenPeerTable
