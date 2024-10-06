import django_tables2 as tables
from django.conf import settings

from peering_manager.tables import PeeringManagerTable, columns

from ..models import ObjectChange

__all__ = ("ObjectChangeTable",)

OBJECT_CHANGE_ACTION = """
{% if record.action == "create" %}
<span class="badge badge-success">Created</span>
{% elif record.action == "update" %}
<span class="badge badge-primary">Updated</span>
{% elif record.action == "delete" %}
<span class="badge badge-danger">Deleted</span>
{% endif %}
"""

OBJECT_CHANGE_OBJECT = """
{% if record.action != 3 and record.changed_object.get_absolute_url %}
<a href="{{ record.changed_object.get_absolute_url }}">{{ record.object_repr }}</a>
{% elif record.action != 3 and record.related_object.get_absolute_url %}
<a href="{{ record.related_object.get_absolute_url }}">{{ record.object_repr }}</a>
{% else %}
{{ record.object_repr }}
{% endif %}
"""

OBJECT_CHANGE_REQUEST_ID = """
<a href="{% url 'core:objectchange_list' %}?request_id={{ value }}">{{ value }}</a>
"""


class ObjectChangeTable(PeeringManagerTable):
    time = columns.DateTimeColumn(linkify=True)
    action = tables.TemplateColumn(template_code=OBJECT_CHANGE_ACTION)
    changed_object_type = tables.Column(verbose_name="Type")
    object_repr = tables.TemplateColumn(
        template_code=OBJECT_CHANGE_OBJECT, verbose_name="Object"
    )
    request_id = tables.TemplateColumn(
        template_code=OBJECT_CHANGE_REQUEST_ID, verbose_name="Request ID"
    )
    actions = columns.ActionsColumn(actions=())

    class Meta(PeeringManagerTable.Meta):
        model = ObjectChange
        fields = (
            "pk",
            "id",
            "time",
            "user_name",
            "changed_object_type",
            "object_repr",
            "request_id",
            "action",
        )
        default_columns = (
            "time",
            "user_name",
            "action",
            "changed_object_type",
            "object_repr",
            "request_id",
        )
