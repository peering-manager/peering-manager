from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectChildrenView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)

from .. import filtersets, forms, tables
from ..models import DataFile, DataSource

__all__ = (
    "DataFileListView",
    "DataFileView",
    "DataFileDeleteView",
    "DataFileBulkDeleteView",
    "DataSourceListView",
    "DataSourceEditView",
    "DataSourceBulkEdit",
    "DataSourceDeleteView",
    "DataSourceBulkDeleteView",
    "DataSourceView",
    "DataSourceFilesView",
)


class DataFileListView(ObjectListView):
    permission_required = "core.view_datafile"
    queryset = DataFile.objects.defer("data")
    filterset = filtersets.DataFileFilterSet
    filterset_form = forms.DataFileFilterForm
    table = tables.DataFileTable
    template_name = "core/datafile/list.html"


class DataFileView(ObjectView):
    permission_required = "core.view_datafile"
    queryset = DataFile.objects.all()
    tab = "main"


class DataFileDeleteView(ObjectDeleteView):
    permission_required = "core.delete_datafile"
    queryset = DataFile.objects.all()


class DataFileBulkDeleteView(BulkDeleteView):
    permission_required = "core.delete_datafile"
    queryset = DataFile.objects.all()
    filterset = filtersets.DataFileFilterSet
    table = tables.DataFileTable


class DataSourceListView(ObjectListView):
    permission_required = "core.view_datasource"
    queryset = DataSource.objects.all()
    filterset = filtersets.DataSourceFilterSet
    filterset_form = forms.DataSourceFilterForm
    table = tables.DataSourceTable
    template_name = "core/datasource/list.html"


class DataSourceEditView(ObjectEditView):
    queryset = DataSource.objects.all()
    form = forms.DataSourceForm


class DataSourceBulkEdit(BulkEditView):
    permission_required = "core.change_datasource"
    queryset = DataSource.objects.all()
    filterset = filtersets.DataSourceFilterSet
    table = tables.DataSourceTable
    form = forms.DataSourceBulkEditForm


class DataSourceDeleteView(ObjectDeleteView):
    permission_required = "core.delete_datasource"
    queryset = DataSource.objects.all()


class DataSourceBulkDeleteView(BulkDeleteView):
    permission_required = "core.delete_datasource"
    queryset = DataSource.objects.all()
    filterset = filtersets.DataSourceFilterSet
    table = tables.DataSourceTable


class DataSourceView(ObjectView):
    permission_required = "core.view_datasource"
    queryset = DataSource.objects.all()
    tab = "main"

    def get_extra_context(self, request, instance):
        return {
            "datafile_count": DataFile.objects.filter(source=instance)
            .defer("data")
            .count(),
        }


class DataSourceFilesView(ObjectChildrenView):
    permission_required = ("core.view_datasource", "core.view_datafile")
    queryset = DataSource.objects.all()
    child_model = DataFile
    filterset = filtersets.DataFileFilterSet
    filterset_form = forms.DataFileFilterForm
    table = tables.DataFileTable
    template_name = "core/datasource/files.html"
    tab = "files"

    def get_children(self, request, parent):
        return (
            DataFile.objects.filter(source=parent)
            .defer("data")
            .prefetch_related("source")
        )
