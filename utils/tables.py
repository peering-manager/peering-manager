import django_tables2 as tables

from django.utils.safestring import mark_safe

from .models import ObjectChange, Tag


OBJECT_CHANGE_TIME = """
<a href="{{ record.get_absolute_url }}">{{ value | date:"SHORT_DATETIME_FORMAT" }}</a>
"""

OBJECT_CHANGE_ACTION = """
{% if record.action == 1 %}
<span class="badge badge-success">Created</span>
{% elif record.action == 2 %}
<span class="badge badge-primary">Updated</span>
{% elif record.action == 3 %}
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

TAG_ACTIONS = """
{% if perms.utils.change_tag %}
<a href="{% url 'utils:tag_edit' slug=record.slug %}" class="btn btn-xs btn-warning"><i class="fas fa-edit"></i></a>
{% endif %}
"""

OBJECT_CHANGE_REQUEST_ID = """
<a href="{% url 'utils:objectchange_list' %}?request_id={{ value }}">{{ value }}</a>
"""


class ActionsColumn(tables.TemplateColumn):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.pop("attrs", {"td": {"class": "text-right"}})
        default = kwargs.pop("default", "")
        orderable = kwargs.pop("orderable", False)
        verbose_name = kwargs.pop("verbose_name", "")
        super().__init__(
            *args,
            attrs=attrs,
            default=default,
            orderable=orderable,
            verbose_name=verbose_name,
            **kwargs
        )


class BaseTable(tables.Table):
    """
    Default table for object lists
    """

    def __init__(self, *args, **kwargs):
        hidden_columns = kwargs.pop("hidden_columns", [])
        super().__init__(*args, **kwargs)

        # Set default empty_text if none was provided
        if self.empty_text is None:
            self.empty_text = "No {} found.".format(
                self._meta.model._meta.verbose_name_plural
            )

        # Hide columns that should not show up
        for column_to_hide in hidden_columns:
            if column_to_hide in self.base_columns:
                self.columns.hide(column_to_hide)

    class Meta:
        attrs = {"class": "table table-sm table-hover table-headings"}


class ColorColumn(tables.Column):
    """
    Display a colored block.
    """

    def render(self, value):
        return mark_safe(
            '<span class="label color-block" style="background-color: #{}">&nbsp;</span>'.format(
                value
            )
        )


class ObjectChangeTable(BaseTable):
    time = tables.TemplateColumn(template_code=OBJECT_CHANGE_TIME)
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


class SelectColumn(tables.CheckBoxColumn):
    def __init__(self, *args, **kwargs):
        default = kwargs.pop("default", "")
        visible = kwargs.pop("visible", False)
        super().__init__(*args, default=default, visible=visible, **kwargs)

    @property
    def header(self):
        return mark_safe('<input type="checkbox" class="toggle" title="Select all" />')


class TagTable(BaseTable):
    pk = SelectColumn()
    name = tables.LinkColumn()
    color = ColorColumn()
    actions = ActionsColumn(template_code=TAG_ACTIONS, verbose_name="")

    class Meta(BaseTable.Meta):
        model = Tag
        fields = ("pk", "name", "slug", "color", "items", "actions")
