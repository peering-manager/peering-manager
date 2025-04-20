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

from ..filtersets import BFDFilterSet
from ..forms import BFDBulkEditForm, BFDFilterForm, BFDForm
from ..models import BFD
from ..tables import BFDTable

__all__ = (
    "BFDBulkDelete",
    "BFDBulkEdit",
    "BFDContext",
    "BFDDelete",
    "BFDEdit",
    "BFDList",
    "BFDView",
)


@register_model_view(model=BFD, name="list", path="", detail=False)
class BFDList(ObjectListView):
    permission_required = "net.view_bfd"
    queryset = BFD.objects.all()
    filterset = BFDFilterSet
    filterset_form = BFDFilterForm
    table = BFDTable
    template_name = "net/bfd/list.html"


@register_model_view(model=BFD)
class BFDView(ObjectView):
    permission_required = "net.view_bfd"
    queryset = BFD.objects.all()


@register_model_view(model=BFD, name="configcontext", path="config-context")
class BFDContext(ObjectConfigContextView):
    permission_required = "net.view_bfd"
    queryset = BFD.objects.all()
    base_template = "net/bfd/_base.html"


@register_model_view(model=BFD, name="add", detail=False)
@register_model_view(model=BFD, name="edit")
class BFDEdit(ObjectEditView):
    queryset = BFD.objects.all()
    form = BFDForm


@register_model_view(model=BFD, name="delete")
class BFDDelete(ObjectDeleteView):
    permission_required = "net.delete_bfd"
    queryset = BFD.objects.all()


@register_model_view(model=BFD, name="bulk_edit", path="edit", detail=False)
class BFDBulkEdit(BulkEditView):
    permission_required = "net.change_bfd"
    queryset = BFD.objects.all()
    filterset = BFDFilterSet
    table = BFDTable
    form = BFDBulkEditForm


@register_model_view(model=BFD, name="bulk_delete", path="delete", detail=False)
class BFDBulkDelete(BulkDeleteView):
    queryset = BFD.objects.all()
    filterset = BFDFilterSet
    table = BFDTable
