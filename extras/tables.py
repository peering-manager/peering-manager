import django_tables2 as tables

from peering_manager.tables import PeeringManagerTable, columns

from .models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    Tag,
    TaggedItem,
    Webhook,
)


class ConfigContextTable(PeeringManagerTable):
    pk = columns.SelectColumn()
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


class TagTable(PeeringManagerTable):
    pk = columns.SelectColumn()
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
    pk = columns.SelectColumn()
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
