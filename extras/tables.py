import django_tables2 as tables

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
    Tag,
    TaggedItem,
)


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
