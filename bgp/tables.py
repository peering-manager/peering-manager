import django_tables2 as tables

from bgp.models import Relationship
from utils.tables import BaseTable, ButtonsColumn, ColourColumn, SelectColumn


class RelationshipTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    color = ColourColumn()
    buttons = ButtonsColumn(Relationship, buttons=("edit", "delete"))

    class Meta(BaseTable.Meta):
        model = Relationship
        fields = ("pk", "name", "slug", "description", "color", "buttons")
        default_columns = ("pk", "name", "color", "buttons")
