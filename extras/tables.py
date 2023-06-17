import django_tables2 as tables
from django.conf import settings

from utils.tables import (
    BaseTable,
    BooleanColumn,
    ButtonsColumn,
    ColourColumn,
    ContentTypeColumn,
    SelectColumn,
)

from .models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    ObjectChange,
    Tag,
    TaggedItem,
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


class ConfigContextTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    is_active = BooleanColumn(verbose_name="Active")
    actions = ButtonsColumn(ConfigContext)

    class Meta(BaseTable.Meta):
        model = ConfigContext
        fields = ("pk", "name", "description", "is_active")
        default_columns = ("name", "description", "is_active")


class ConfigContextAssignmentTable(BaseTable):
    content_type = ContentTypeColumn(verbose_name="Object Type")
    object = tables.Column(linkify=True, orderable=False)
    config_context = tables.Column(linkify=True)
    actions = ButtonsColumn(model=ConfigContextAssignment, buttons=("edit", "delete"))

    class Meta(BaseTable.Meta):
        model = ConfigContextAssignment
        fields = ("content_type", "object", "config_context", "weight", "actions")
        default_columns = (
            "content_type",
            "object",
            "config_context",
            "weight",
            "actions",
        )


class ExportTemplateTable(BaseTable):
    pk = SelectColumn()
    content_type = ContentTypeColumn()
    name = tables.Column(linkify=True)
    jinja2_trim = BooleanColumn(verbose_name="Trim")
    jinja2_lstrip = BooleanColumn(verbose_name="Lstrip")
    actions = ButtonsColumn(ExportTemplate)

    class Meta(BaseTable.Meta):
        model = ExportTemplate
        fields = ("name", "content_type", "description", "jinja2_trim", "jinja2_lstrip")
        default_columns = (
            "name",
            "content_type",
            "description",
            "jinja2_trim",
            "jinja2_lstrip",
        )


class IXAPITable(BaseTable):
    name = tables.Column(linkify=True)
    url = tables.URLColumn()
    actions = ButtonsColumn(IXAPI)

    class Meta(BaseTable.Meta):
        model = IXAPI
        fields = ("name", "url", "api_key", "actions")
        default_columns = ("name", "url", "api_key", "actions")


class ObjectChangeTable(BaseTable):
    time = tables.DateTimeColumn(linkify=True, format=settings.SHORT_DATETIME_FORMAT)
    action = tables.TemplateColumn(template_code=OBJECT_CHANGE_ACTION)
    changed_object_type = tables.Column(verbose_name="Type")
    object_repr = tables.TemplateColumn(
        template_code=OBJECT_CHANGE_OBJECT, verbose_name="Object"
    )
    request_id = tables.TemplateColumn(
        template_code=OBJECT_CHANGE_REQUEST_ID, verbose_name="Request ID"
    )

    class Meta(BaseTable.Meta):
        model = ObjectChange
        fields = (
            "time",
            "user_name",
            "action",
            "changed_object_type",
            "object_repr",
            "request_id",
        )
        default_columns = (
            "time",
            "user_name",
            "action",
            "changed_object_type",
            "object_repr",
            "request_id",
        )


class TagTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    color = ColourColumn()
    actions = ButtonsColumn(Tag, buttons=("edit", "delete"))

    class Meta(BaseTable.Meta):
        model = Tag
        fields = ("pk", "name", "slug", "color", "items", "actions")
        default_columns = ("pk", "name", "color", "items", "actions")


class TaggedItemTable(BaseTable):
    id = tables.Column(
        verbose_name="ID",
        linkify=lambda record: record.content_object.get_absolute_url(),
        accessor="content_object__id",
    )
    content_type = ContentTypeColumn(verbose_name="Type")
    content_object = tables.Column(linkify=True, orderable=False, verbose_name="Object")

    class Meta(BaseTable.Meta):
        model = TaggedItem
        fields = ("id", "content_type", "content_object")
