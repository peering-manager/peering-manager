from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import ExportTemplateFilterSet
from ..forms import ExportTemplateFilterForm, ExportTemplateForm
from ..models import ExportTemplate
from ..tables import ExportTemplateTable

__all__ = (
    "ExportTemplateBulkDeleteView",
    "ExportTemplateDeleteView",
    "ExportTemplateEditView",
    "ExportTemplateListView",
    "ExportTemplateView",
)


@register_model_view(ExportTemplate, name="list", path="", detail=False)
class ExportTemplateListView(ObjectListView):
    permission_required = "extras.view_exporttemplate"
    queryset = ExportTemplate.objects.all()
    filterset = ExportTemplateFilterSet
    filterset_form = ExportTemplateFilterForm
    table = ExportTemplateTable
    template_name = "extras/exporttemplate/list.html"


@register_model_view(ExportTemplate)
class ExportTemplateView(ObjectView):
    permission_required = "extras.view_exporttemplate"
    queryset = ExportTemplate.objects.all()


@register_model_view(model=ExportTemplate, name="add", detail=False)
@register_model_view(model=ExportTemplate, name="edit")
class ExportTemplateEditView(ObjectEditView):
    queryset = ExportTemplate.objects.all()
    form = ExportTemplateForm


@register_model_view(ExportTemplate, name="delete")
class ExportTemplateDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_exporttemplate"
    queryset = ExportTemplate.objects.all()


@register_model_view(ExportTemplate, name="bulk_delete", detail=False)
class ExportTemplateBulkDeleteView(BulkDeleteView):
    permission_required = "extras.delete_exporttemplate"
    queryset = ExportTemplate.objects.all()
    filterset = ExportTemplateFilterSet
    table = ExportTemplateTable
