import django_tables2 as tables

from peering_manager.tables import PeeringManagerTable, columns

from ..models import Relationship

__all__ = ("RelationshipTable",)


class RelationshipTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    color = columns.ColourColumn()

    class Meta(PeeringManagerTable.Meta):
        model = Relationship
        fields = ("pk", "id", "name", "slug", "description", "color", "actions")
        default_columns = ("pk", "name", "color", "actions")
