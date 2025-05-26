from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import ViewTab, register_model_view

from ..filtersets import ConfigContextFilterSet
from ..forms import ConfigContextFilterForm, ConfigContextForm
from ..models import ConfigContext, ConfigContextAssignment
from ..tables import ConfigContextAssignmentTable, ConfigContextTable

__all__ = (
    "ConfigContextBulkDeleteView",
    "ConfigContextDeleteView",
    "ConfigContextEditView",
    "ConfigContextListView",
    "ConfigContextView",
    "ObjectConfigContextView",
)


@register_model_view(ConfigContext, name="list", path="", detail=False)
class ConfigContextListView(ObjectListView):
    permission_required = "extras.view_configcontext"
    queryset = ConfigContext.objects.all()
    filterset = ConfigContextFilterSet
    filterset_form = ConfigContextFilterForm
    table = ConfigContextTable
    template_name = "extras/configcontext/list.html"


@register_model_view(ConfigContext)
class ConfigContextView(ObjectView):
    permission_required = "extras.view_configcontext"
    queryset = ConfigContext.objects.all()

    def get_extra_context(self, request, instance):
        if request.GET.get("format") in ("json", "yaml"):
            format = request.GET.get("format")
            if request.user.is_authenticated:
                request.user.preferences.set(
                    "configcontext.format", format, commit=True
                )
        elif request.user.is_authenticated:
            format = request.user.preferences.get("configcontext.format", "json")
        else:
            format = "json"

        config_context_assignments = ConfigContextAssignment.objects.filter(
            config_context=instance
        )
        assignments_table = ConfigContextAssignmentTable(config_context_assignments)
        assignments_table.columns.hide("config_context")
        assignments_table.configure(request)

        return {
            "assignments_table": assignments_table,
            "assignment_count": ConfigContextAssignment.objects.filter(
                config_context=instance
            ).count(),
            "configcontext_format": format,
        }


@register_model_view(model=ConfigContext, name="add", detail=False)
@register_model_view(model=ConfigContext, name="edit")
class ConfigContextEditView(ObjectEditView):
    queryset = ConfigContext.objects.all()
    form = ConfigContextForm


@register_model_view(model=ConfigContext, name="delete")
class ConfigContextDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_configcontext"
    queryset = ConfigContext.objects.all()


@register_model_view(ConfigContext, name="bulk_delete", path="delete", detail=False)
class ConfigContextBulkDeleteView(BulkDeleteView):
    permission_required = "extras.delete_configcontext"
    queryset = ConfigContext.objects.all()
    filterset = ConfigContextFilterSet
    table = ConfigContextTable


class ObjectConfigContextView(ObjectView):
    base_template = None
    template_name = "extras/object_configcontext.html"
    tab = ViewTab(
        label="Config Context", permission="extras.view_configcontext", weight=9800
    )

    def get_extra_context(self, request, instance):
        if request.GET.get("format") in ("json", "yaml"):
            format = request.GET.get("format")
            if request.user.is_authenticated:
                request.user.preferences.set(
                    "configcontext.format", format, commit=True
                )
        elif request.user.is_authenticated:
            format = request.user.preferences.get("configcontext.format", "json")
        else:
            format = "json"

        return {
            "configcontext_format": format,
            "base_template": self.base_template,
            "rendered_context": instance.get_config_context(),
        }
