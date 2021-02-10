import django_tables2 as tables
from django.core.exceptions import FieldDoesNotExist
from django.db.models import ForeignKey
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

OBJECT_CHANGE_REQUEST_ID = """
<a href="{% url 'utils:objectchange_list' %}?request_id={{ value }}">{{ value }}</a>
"""


class BaseTable(tables.Table):
    """
    Default table for object lists
    """

    class Meta:
        attrs = {"class": "table table-sm table-hover table-headings"}

    def __init__(self, *args, columns=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Set default empty_text if none was provided
        if self.empty_text is None:
            self.empty_text = f"No {self._meta.model._meta.verbose_name_plural} found."

        # Hide columns that should not be displayed by default
        default_columns = getattr(self.Meta, "default_columns", list())
        for column in self.columns:
            if column.name not in default_columns:
                self.columns.hide(column.name)

        # Apply custom column ordering
        if columns is not None:
            # PK and actions columns are to be delt with differently
            pk = self.base_columns.pop("pk", None)
            actions = self.base_columns.pop("actions", None)

            for name, column in self.base_columns.items():
                if name in columns:
                    self.columns.show(name)
                else:
                    self.columns.hide(name)
            self.sequence = [c for c in columns if c in self.base_columns]

            # Always include PK as first column
            if pk:
                self.base_columns["pk"] = pk
                self.sequence.insert(0, "pk")
            # Always include actions as last column
            if actions:
                self.base_columns["actions"] = actions
                self.sequence.append("actions")

        # Update the table's QuerySet to ensure related fields prefeching
        if isinstance(self.data, tables.data.TableQuerysetData):
            model = getattr(self.Meta, "model")
            prefetch_fields = []
            for column in self.columns:
                if column.visible:
                    field_path = column.accessor.split(".")
                    try:
                        model_field = model._meta.get_field(field_path[0])
                        if isinstance(model_field, ForeignKey):
                            prefetch_fields.append("__".join(field_path))
                    except FieldDoesNotExist:
                        pass
            self.data.data = self.data.data.prefetch_related(None).prefetch_related(
                *prefetch_fields
            )

    @property
    def configurable_columns(self):
        selected_columns = [
            (name, self.columns[name].verbose_name)
            for name in self.sequence
            if name not in ["pk", "actions"]
        ]
        available_columns = [
            (name, column.verbose_name)
            for name, column in self.columns.items()
            if name not in self.sequence and name not in ["pk", "actions"]
        ]
        return selected_columns + available_columns

    @property
    def visible_columns(self):
        return [name for name in self.sequence if self.columns[name].visible]


class BooleanColumn(tables.BooleanColumn):
    """
    Simple column customizing boolean value rendering using icons and Bootstrap colors.
    """

    def render(self, value, record, bound_column):
        html = '<i class="fas fa-check text-success"></i>'
        if not self._get_bool_value(record, value, bound_column):
            html = '<i class="fas fa-times text-danger"></i>'

        return mark_safe(html)


class ButtonsColumn(tables.TemplateColumn):
    """
    Renders buttons for an object, in a row of a table.
    """

    attrs = {"td": {"class": "text-right text-nowrap"}}
    # Note that braces are escaped to allow for string formatting prior to template rendering
    template_code = """
    {{% if "changelog" in buttons %}}
    <a href="{{% url '{app_label}:{model_name}_changelog' {pk_field}=record.{pk_field} %}}" class="btn btn-xs btn-secondary" title="Change log">
      <i class="fas fa-history"></i>
    </a>
    {{% endif %}}
    {{% if "edit" in buttons and perms.{app_label}.change_{model_name} %}}
    <a href="{{% url '{app_label}:{model_name}_edit' {pk_field}=record.{pk_field} %}}?return_url={{{{ request.path }}}}{{{{ return_url_extra }}}}" class="btn btn-xs btn-warning" title="Edit">
      <i class="fas fa-edit"></i>
    </a>
    {{% endif %}}
    {{% if "delete" in buttons and perms.{app_label}.delete_{model_name} %}}
    <a href="{{% url '{app_label}:{model_name}_delete' {pk_field}=record.{pk_field} %}}?return_url={{{{ request.path }}}}{{{{ return_url_extra }}}}" class="btn btn-xs btn-danger" title="Delete">
      <i class="fas fa-trash-alt"></i>
    </a>
    {{% endif %}}
    """

    def __init__(
        self,
        model,
        *args,
        pk_field="pk",
        buttons=("changelog", "edit", "delete"),
        prepend_template=None,
        append_template=None,
        return_url_extra="",
        **kwargs,
    ):
        if prepend_template:
            prepend_template = prepend_template.replace("{", "{{").replace("}", "}}")
            self.template_code = prepend_template + self.template_code
        if append_template:
            append_template = append_template.replace("{", "{{").replace("}", "}}")
            self.template_code = self.template_code + append_template

        template_code = self.template_code.format(
            app_label=model._meta.app_label,
            model_name=model._meta.model_name,
            pk_field=pk_field,
            buttons=buttons,
        )
        super().__init__(template_code=template_code, *args, **kwargs)

        self.extra_context.update(
            {"buttons": buttons, "return_url_extra": return_url_extra}
        )

    def header(self):
        return ""


class ColourColumn(tables.Column):
    """
    Displays a coloured block.
    """

    def render(self, value):
        return mark_safe(
            f'<span class="label color-block" style="background-color: #{value}">&nbsp;</span>'
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
        default_columns = (
            "time",
            "user_name",
            "action",
            "changed_object_type",
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


class TagColumn(tables.TemplateColumn):
    """
    Displays a list of tags assigned to an object.
    """

    template_code = """
    {% for tag in value.all %}
    {% include 'utils/templatetags/tag.html' %}
    {% empty %}
    <span class="text-muted">&mdash;</span>
    {% endfor %}
    """

    def __init__(self, url_name=None):
        super().__init__(
            template_code=self.template_code, extra_context={"url_name": url_name}
        )


class TagTable(BaseTable):
    pk = SelectColumn()
    name = tables.LinkColumn()
    color = ColourColumn()
    buttons = ButtonsColumn(Tag, buttons=("edit", "delete"), pk_field="slug")

    class Meta(BaseTable.Meta):
        model = Tag
        fields = ("pk", "name", "slug", "color", "items", "buttons")
        default_columns = ("pk", "name", "color", "items", "buttons")
