import django_tables2 as tables

from peering_manager.registry import DATA_BACKENDS_KEY, registry
from peering_manager.tables import PeeringManagerTable, columns

from ..models import DataFile, DataSource

__all__ = ("DataFileTable", "DataSourceTable")


class BackendTypeColumn(tables.Column):
    def render(self, value):
        try:
            return registry[DATA_BACKENDS_KEY][value].label
        except KeyError:
            return value

    def value(self, value):
        return value


class DataFileTable(PeeringManagerTable):
    source = tables.Column(linkify=True)
    path = tables.Column(linkify=True)
    updated = columns.DateTimeColumn()
    actions = columns.ActionsColumn(actions=("delete",))

    class Meta(PeeringManagerTable.Meta):
        model = DataFile
        fields = ("pk", "id", "source", "path", "updated", "size", "hash")
        default_columns = ("pk", "source", "path", "size", "updated")


class DataSourceTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    type = BackendTypeColumn()
    status = columns.ChoiceFieldColumn()
    enabled = columns.BooleanColumn()
    tags = columns.TagColumn(url_name="core:datasource_list")
    file_count = tables.Column(verbose_name="Files")

    class Meta(PeeringManagerTable.Meta):
        model = DataSource
        fields = (
            "pk",
            "id",
            "name",
            "type",
            "status",
            "enabled",
            "source_url",
            "description",
            "comments",
            "parameters",
            "created",
            "updated",
            "file_count",
        )
        default_columns = (
            "pk",
            "name",
            "type",
            "status",
            "enabled",
            "description",
            "file_count",
        )
