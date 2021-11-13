from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect, render

from utils.views import (
    AddOrEditView,
    BulkDeleteView,
    DeleteView,
    DetailsView,
    ModelListView,
    PermissionRequiredMixin,
)

from .filters import IXAPIFilterSet, JobResultFilterSet
from .forms import IXAPIFilterForm, IXAPIForm, JobResultFilterForm
from .models import IXAPI, JobResult
from .tables import IXAPITable, JobResultTable


class IXAPIListView(PermissionRequiredMixin, ModelListView):
    permission_required = "extras.view_ixapi"
    queryset = IXAPI.objects.all()
    filter = IXAPIFilterSet
    filter_form = IXAPIFilterForm
    table = IXAPITable
    template = "extras/ixapi/list.html"


class IXAPIView(DetailsView):
    permission_required = "extras.view_ixapi"
    queryset = IXAPI.objects.all()


class IXAPIAddView(PermissionRequiredMixin, AddOrEditView):
    permission_required = "extras.add_ixapi"
    model = IXAPI
    form = IXAPIForm
    return_url = "extras:ixapi_list"
    template = "extras/ixapi/add_edit.html"


class IXAPIEditView(PermissionRequiredMixin, AddOrEditView):
    permission_required = "extras.change_ixapi"
    model = IXAPI
    form = IXAPIForm
    template = "extras/ixapi/add_edit.html"


class IXAPIDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = "extras.delete_ixapi"
    model = IXAPI
    return_url = "extras:ixapi_list"


class JobResultListView(PermissionRequiredMixin, ModelListView):
    permission_required = "extras.view_jobresult"
    queryset = JobResult.objects.all()
    filter = JobResultFilterSet
    filter_form = JobResultFilterForm
    table = JobResultTable
    action_buttons = ()
    template = "extras/jobresult/list.html"


class JobResultDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = "extras.delete_jobresult"
    model = JobResult
    return_url = "extras:jobresult_list"


class JobResultBulkDeleteView(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "extras.delete_jobresult"
    model = JobResult
    table = JobResultTable


class JobResultView(DetailsView):
    permission_required = "extras.view_jobresult"
    queryset = JobResult.objects.all()
