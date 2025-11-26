import django_tables2 as tables

from peering_manager.tables import PeeringManagerTable, columns

from ..models import Community

__all__ = ("CommunityColumn", "CommunityTable")


COMMUNITY_TYPE = """
{% if record.type %}
  {{ record.get_type_html }}
{% else %}
  <span class="badge text-bg-secondary">Not set</span>
{% endif %}
"""


class CommunityColumn(tables.ManyToManyColumn):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, linkify_item=True, **kwargs)

    def transform(self, obj):
        return obj.name if obj else None


class CommunityTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    type = tables.TemplateColumn(template_code=COMMUNITY_TYPE)
    tags = columns.TagColumn(url_name="bgp:community_list")

    class Meta(PeeringManagerTable.Meta):
        model = Community
        fields = ("pk", "name", "slug", "value", "type", "tags", "actions")
        default_columns = ("pk", "name", "value", "type", "actions")
