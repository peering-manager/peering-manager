import django_tables2 as tables
from django.conf import settings

from peering_manager.tables import PeeringManagerTable, columns

from .models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    ObjectChange,
    Tag,
    TaggedItem,
    Webhook,
)

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
<a href="{% url 'extras:objectchange_list' %}?request_id={{ value }}">{{ value }}</a>
"""


class ConfigContextTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    is_active = columns.BooleanColumn(verbose_name="Active")

    class Meta(PeeringManagerTable.Meta):
        model = ConfigContext
        fields = ("pk", "id", "name", "description", "is_active")
        default_columns = ("name", "description", "is_active")


class ConfigContextAssignmentTable(PeeringManagerTable):
    content_type = columns.ContentTypeColumn(verbose_name="Object Type")
    object = tables.Column(linkify=True, orderable=False)
    config_context = tables.Column(linkify=True)
    actions = columns.ActionsColumn(actions=("edit", "delete"))

    class Meta(PeeringManagerTable.Meta):
        model = ConfigContextAssignment
        fields = ("id", "content_type", "object", "config_context", "weight", "actions")
        default_columns = (
            "content_type",
            "object",
            "config_context",
            "weight",
            "actions",
        )


class ExportTemplateTable(PeeringManagerTable):
    content_type = columns.ContentTypeColumn()
    name = tables.Column(linkify=True)
    jinja2_trim = columns.BooleanColumn(verbose_name="Trim")
    jinja2_lstrip = columns.BooleanColumn(verbose_name="Lstrip")

    class Meta(PeeringManagerTable.Meta):
        model = ExportTemplate
        fields = (
            "id",
            "name",
            "content_type",
            "description",
            "jinja2_trim",
            "jinja2_lstrip",
        )
        default_columns = (
            "name",
            "content_type",
            "description",
            "jinja2_trim",
            "jinja2_lstrip",
        )


class IXAPITable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    url = tables.URLColumn()

    class Meta(PeeringManagerTable.Meta):
        model = IXAPI
        fields = ("id", "name", "url", "api_key", "actions")
        default_columns = ("name", "url", "api_key", "actions")


class ObjectChangeTable(PeeringManagerTable):
    time = tables.DateTimeColumn(linkify=True, format=settings.SHORT_DATETIME_FORMAT)
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


class TagTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    color = columns.ColourColumn()

    class Meta(PeeringManagerTable.Meta):
        model = Tag
        fields = ("pk", "id", "name", "slug", "color", "items", "actions")
        default_columns = ("pk", "name", "color", "items", "actions")


class TaggedItemTable(PeeringManagerTable):
    id = tables.Column(
        verbose_name="ID",
        linkify=lambda record: record.content_object.get_absolute_url(),
        accessor="content_object__id",
    )
    content_type = columns.ContentTypeColumn(verbose_name="Type")
    content_object = tables.Column(linkify=True, orderable=False, verbose_name="Object")
    actions = columns.ActionsColumn(actions=())

    class Meta(PeeringManagerTable.Meta):
        model = TaggedItem
        fields = ("id", "content_type", "content_object")


class WebhookTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    content_types = columns.ContentTypesColumn()
    enabled = columns.BooleanColumn()
    type_create = columns.BooleanColumn(verbose_name="Create")
    type_update = columns.BooleanColumn(verbose_name="Update")
    type_delete = columns.BooleanColumn(verbose_name="Delete")
    ssl_validation = columns.BooleanColumn(verbose_name="SSL Validation")
    actions = columns.ActionsColumn()

    class Meta(PeeringManagerTable.Meta):
        model = Webhook
        fields = (
            "pk",
            "id",
            "name",
            "content_types",
            "enabled",
            "type_create",
            "type_update",
            "type_delete",
            "http_method",
            "payload_url",
            "secret",
            "ssl_validation",
            "ca_file_path",
            "created",
            "last_updated",
        )
        default_columns = (
            "pk",
            "name",
            "content_types",
            "enabled",
            "type_create",
            "type_update",
            "type_delete",
            "http_method",
            "payload_url",
        )
