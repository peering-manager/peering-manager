from peering_manager.views.generics import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectListView,
    ObjectView,
)

from . import filtersets, forms, tables
from .models import Job


class JobListView(ObjectListView):
    permission_required = "core.view_job"
    queryset = Job.objects.all()
    filterset = filtersets.JobFilterSet
    filterset_form = forms.JobFilterForm
    table = tables.JobTable
    template_name = "core/job/list.html"


class JobDeleteView(ObjectDeleteView):
    permission_required = "core.delete_job"
    queryset = Job.objects.all()


class JobBulkDeleteView(BulkDeleteView):
    permission_required = "core.delete_job"
    queryset = Job.objects.all()
    filterset = filtersets.JobFilterSet
    table = tables.JobTable


class JobView(ObjectView):
    permission_required = "core.view_job"
    queryset = Job.objects.all()
