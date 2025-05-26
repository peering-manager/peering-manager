from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from .. import filtersets, forms, tables
from ..models import Job

__all__ = ("JobBulkDeleteView", "JobDeleteView", "JobListView", "JobView")


@register_model_view(Job, name="list", path="", detail=False)
class JobListView(ObjectListView):
    permission_required = "core.view_job"
    queryset = Job.objects.all()
    filterset = filtersets.JobFilterSet
    filterset_form = forms.JobFilterForm
    table = tables.JobTable
    template_name = "core/job/list.html"


@register_model_view(Job)
class JobView(ObjectView):
    permission_required = "core.view_job"
    queryset = Job.objects.all()


@register_model_view(Job, name="delete")
class JobDeleteView(ObjectDeleteView):
    permission_required = "core.delete_job"
    queryset = Job.objects.all()


@register_model_view(Job, name="bulk_delete", path="delete", detail=False)
class JobBulkDeleteView(BulkDeleteView):
    permission_required = "core.delete_job"
    queryset = Job.objects.all()
    filterset = filtersets.JobFilterSet
    table = tables.JobTable
