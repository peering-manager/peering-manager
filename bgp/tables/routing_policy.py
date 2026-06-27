import django_tables2 as tables
from django.utils.safestring import mark_safe

from peering_manager.tables import PeeringManagerTable, columns

from ..models import RoutingPolicy
from .community import CommunityColumn

__all__ = ("RoutingPolicyColumn", "RoutingPolicyTable")


ROUTING_POLICY_TYPE = "{{ record.get_type_html }}"


class RoutingPolicyColumn(tables.ManyToManyColumn):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            default=mark_safe('<span class="text-muted">&mdash;</span>'),
            separator=" ",
            transform=lambda p: p.get_type_html(display_name=True),
            **kwargs,
        )


class RoutingPolicyTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    type = tables.TemplateColumn(template_code=ROUTING_POLICY_TYPE)
    communities = CommunityColumn()
    tags = columns.TagColumn(url_name="bgp:routingpolicy_list")

    class Meta(PeeringManagerTable.Meta):
        model = RoutingPolicy
        fields = (
            "pk",
            "id",
            "name",
            "slug",
            "description",
            "type",
            "weight",
            "address_family",
            "communities",
            "tags",
            "actions",
        )
        default_columns = ("pk", "name", "type", "weight", "address_family", "actions")
