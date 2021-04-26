from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect, render

from utils.views import (
    BulkDeleteView,
    DeleteView,
    DetailsView,
    ModelListView,
    PermissionRequiredMixin,
)

from .filters import JobResultFilterSet
from .forms import JobResultFilterForm
from .models import JobResult
from .tables import JobResultTable


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
    queryset = JobResult.objects.all()


class JobResultBulkDeleteView(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "extras.delete_jobresult"
    model = JobResult
    table = JobResultTable


class JobResultView(DetailsView):
    permission_required = "extras.view_jobresult"
    queryset = JobResult.objects.all()
