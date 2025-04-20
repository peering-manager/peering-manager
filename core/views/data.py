from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectChildrenView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import ViewTab, register_model_view

from .. import filtersets, forms, tables
from ..models import DataFile, DataSource

__all__ = (
    "DataFileBulkDeleteView",
    "DataFileDeleteView",
    "DataFileListView",
    "DataFileView",
    "DataSourceBulkDeleteView",
    "DataSourceBulkEdit",
    "DataSourceDeleteView",
    "DataSourceEditView",
    "DataSourceFilesView",
    "DataSourceListView",
    "DataSourceView",
)


@register_model_view(DataFile, name="list", path="", detail=False)
class DataFileListView(ObjectListView):
    permission_required = "core.view_datafile"
    queryset = DataFile.objects.defer("data")
    filterset = filtersets.DataFileFilterSet
    filterset_form = forms.DataFileFilterForm
    table = tables.DataFileTable
    template_name = "core/datafile/list.html"


@register_model_view(DataFile)
class DataFileView(ObjectView):
    permission_required = "core.view_datafile"
    queryset = DataFile.objects.all()


@register_model_view(DataFile, name="delete")
class DataFileDeleteView(ObjectDeleteView):
    permission_required = "core.delete_datafile"
    queryset = DataFile.objects.all()


@register_model_view(DataFile, name="bulk_delete", path="delete", detail=False)
class DataFileBulkDeleteView(BulkDeleteView):
    permission_required = "core.delete_datafile"
    queryset = DataFile.objects.all()
    filterset = filtersets.DataFileFilterSet
    table = tables.DataFileTable


@register_model_view(DataSource, name="list", path="", detail=False)
class DataSourceListView(ObjectListView):
    permission_required = "core.view_datasource"
    queryset = DataSource.objects.all()
    filterset = filtersets.DataSourceFilterSet
    filterset_form = forms.DataSourceFilterForm
    table = tables.DataSourceTable
    template_name = "core/datasource/list.html"


@register_model_view(DataSource)
class DataSourceView(ObjectView):
    permission_required = "core.view_datasource"
    queryset = DataSource.objects.all()

    def get_extra_context(self, request, instance):
        return {
            "datafile_count": DataFile.objects.filter(source=instance)
            .defer("data")
            .count(),
        }


@register_model_view(DataSource, name="add", detail=False)
@register_model_view(DataSource, name="edit")
class DataSourceEditView(ObjectEditView):
    queryset = DataSource.objects.all()
    form = forms.DataSourceForm


@register_model_view(DataSource, name="delete")
class DataSourceDeleteView(ObjectDeleteView):
    permission_required = "core.delete_datasource"
    queryset = DataSource.objects.all()


@register_model_view(DataSource, name="bulk_edit", path="edit", detail=False)
class DataSourceBulkEdit(BulkEditView):
    permission_required = "core.change_datasource"
    queryset = DataSource.objects.all()
    filterset = filtersets.DataSourceFilterSet
    table = tables.DataSourceTable
    form = forms.DataSourceBulkEditForm


@register_model_view(DataSource, name="bulk_delete", path="delete", detail=False)
class DataSourceBulkDeleteView(BulkDeleteView):
    permission_required = "core.delete_datasource"
    queryset = DataSource.objects.all()
    filterset = filtersets.DataSourceFilterSet
    table = tables.DataSourceTable


@register_model_view(DataSource, name="files")
class DataSourceFilesView(ObjectChildrenView):
    permission_required = ("core.view_datasource", "core.view_datafile")
    queryset = DataSource.objects.all()
    child_model = DataFile
    filterset = filtersets.DataFileFilterSet
    filterset_form = forms.DataFileFilterForm
    table = tables.DataFileTable
    template_name = "core/datasource/files.html"
    tab = ViewTab(label="Files", permission="core.view_datafile")

    def get_children(self, request, parent):
        return (
            DataFile.objects.filter(source=parent)
            .defer("data")
            .prefetch_related("source")
        )
