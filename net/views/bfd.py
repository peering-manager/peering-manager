from extras.views import ObjectConfigContextView
from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)

from ..filtersets import BFDFilterSet
from ..forms import BFDBulkEditForm, BFDFilterForm, BFDForm
from ..models import BFD
from ..tables import BFDTable

__all__ = (
    "BFDList",
    "BFDView",
    "BFDContext",
    "BFDEdit",
    "BFDBulkEdit",
    "BFDDelete",
    "BFDBulkDelete",
)


class BFDList(ObjectListView):
    permission_required = "net.view_bfd"
    queryset = BFD.objects.all()
    filterset = BFDFilterSet
    filterset_form = BFDFilterForm
    table = BFDTable
    template_name = "net/bfd/list.html"


class BFDView(ObjectView):
    permission_required = "net.view_bfd"
    queryset = BFD.objects.all()
    tab = "main"


class BFDContext(ObjectConfigContextView):
    permission_required = "net.view_bfd"
    queryset = BFD.objects.all()
    base_template = "net/bfd/_base.html"


class BFDEdit(ObjectEditView):
    queryset = BFD.objects.all()
    form = BFDForm


class BFDBulkEdit(BulkEditView):
    permission_required = "net.change_bfd"
    queryset = BFD.objects.all()
    filterset = BFDFilterSet
    table = BFDTable
    form = BFDBulkEditForm


class BFDDelete(ObjectDeleteView):
    permission_required = "net.delete_bfd"
    queryset = BFD.objects.all()


class BFDBulkDelete(BulkDeleteView):
    queryset = BFD.objects.all()
    filterset = BFDFilterSet
    table = BFDTable
