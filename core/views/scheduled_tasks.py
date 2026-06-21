from django.contrib import messages
from django.shortcuts import redirect

from peering_manager.views.generic import (
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from peering_manager.views.generic.base import BaseObjectView
from utils.views import register_model_view

from .. import filtersets, forms, tables
from ..models import ScheduledTask
from ..scheduling import run_now

__all__ = (
    "ScheduledTaskDeleteView",
    "ScheduledTaskEditView",
    "ScheduledTaskListView",
    "ScheduledTaskRunView",
    "ScheduledTaskView",
)


@register_model_view(ScheduledTask, name="list", path="", detail=False)
class ScheduledTaskListView(ObjectListView):
    permission_required = "core.view_scheduledtask"
    queryset = ScheduledTask.objects.all()
    filterset = filtersets.ScheduledTaskFilterSet
    table = tables.ScheduledTaskTable
    template_name = "core/scheduledtask/list.html"


@register_model_view(ScheduledTask)
class ScheduledTaskView(ObjectView):
    permission_required = "core.view_scheduledtask"
    queryset = ScheduledTask.objects.all()


@register_model_view(ScheduledTask, name="add", detail=False)
@register_model_view(ScheduledTask, name="edit")
class ScheduledTaskEditView(ObjectEditView):
    queryset = ScheduledTask.objects.all()
    form = forms.ScheduledTaskForm


@register_model_view(ScheduledTask, name="delete")
class ScheduledTaskDeleteView(ObjectDeleteView):
    permission_required = "core.delete_scheduledtask"
    queryset = ScheduledTask.objects.all()


@register_model_view(ScheduledTask, name="run", path="run")
class ScheduledTaskRunView(BaseObjectView):
    permission_required = "core.change_scheduledtask"
    queryset = ScheduledTask.objects.all()

    def post(self, request, **kwargs):
        instance = self.get_object(**kwargs)
        run_now(instance.task)
        messages.success(request, f"Queued an immediate run of {instance}.")
        return redirect(instance.get_absolute_url())
