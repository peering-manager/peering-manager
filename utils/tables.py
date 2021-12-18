import django_tables2 as tables
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import RelatedField
from django.utils.safestring import mark_safe

from .models import ObjectChange, Tag

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
<a href="{% url 'utils:objectchange_list' %}?request_id={{ value }}">{{ value }}</a>
"""


def linkify_phone(value):
    if value is None:
        return None
    return f"tel:{value}"


class BaseTable(tables.Table):
    """
    Default table for object lists
    """

    class Meta:
        attrs = {"class": "table table-sm table-hover table-headings"}

    def __init__(self, *args, user=None, extra_columns=None, **kwargs):
        super().__init__(*args, extra_columns=extra_columns, **kwargs)

        # Set default empty_text if none was provided
        if self.empty_text is None:
            self.empty_text = f"No {self._meta.model._meta.verbose_name_plural} found."

        # Hide columns that should not be displayed by default
        default_columns = getattr(self.Meta, "default_columns", list())
        for column in self.columns:
            if column.name not in default_columns:
                self.columns.hide(column.name)

        if user is not None and not isinstance(user, AnonymousUser):
            selected_columns = user.preferences.get(
                f"tables.{self.__class__.__name__}.columns".lower()
            )

            if selected_columns:
                # Show only persistent or selected columns
                for name, column in self.columns.items():
                    if name in ["pk", "actions", *selected_columns]:
                        self.columns.show(name)
                    else:
                        self.columns.hide(name)

                # Rearrange the sequence to list selected columns first, followed by
                # all remaining columns
                self.sequence = [
                    *[c for c in selected_columns if c in self.columns.names()],
                    *[c for c in self.columns.names() if c not in selected_columns],
                ]

                # PK column should always come first
                if "pk" in self.sequence:
                    self.sequence.remove("pk")
                    self.sequence.insert(0, "pk")

                # Actions column should always come last
                if "actions" in self.sequence:
                    self.sequence.remove("actions")
                    self.sequence.append("actions")

        # Update the table's QuerySet to ensure related fields prefeching
        if isinstance(self.data, tables.data.TableQuerysetData):
            prefetch_fields = []
            for column in self.columns:
                if column.visible:
                    model = getattr(self.Meta, "model")
                    accessor = column.accessor
                    prefetch_path = []
                    for field_name in accessor.split(accessor.SEPARATOR):
                        try:
                            field = model._meta.get_field(field_name)
                        except FieldDoesNotExist:
                            break
                        if isinstance(field, RelatedField):
                            # Follow ForeignKeys to the related model
                            prefetch_path.append(field_name)
                            model = field.remote_field.model
                        elif isinstance(field, GenericForeignKey):
                            # Can't prefetch beyond a GenericForeignKey
                            prefetch_path.append(field_name)
                            break

                    if prefetch_path:
                        prefetch_fields.append("__".join(prefetch_path))

            self.data.data = self.data.data.prefetch_related(None).prefetch_related(
                *prefetch_fields
            )

    def _get_columns(self, flat=False, visible=True):
        columns = []
        for name, column in self.columns.items():
            if column.visible == visible and name not in ["pk", "actions"]:
                if flat:
                    columns.append(name)
                else:
                    columns.append((name, column.verbose_name))
        return columns

    @property
    def available_columns(self):
        return self._get_columns() + self._get_columns(visible=False)

    @property
    def selected_columns(self):
        return self._get_columns(flat=True, visible=True)

    @property
    def objects_count(self):
        """
        Returns the total number of real objects represented by the table.
        """
        if not hasattr(self, "_objects_count"):
            self._objects_count = sum(1 for obj in self.data if hasattr(obj, "pk"))
        return self._objects_count


class BooleanColumn(tables.BooleanColumn):
    """
    Simple column customizing boolean value rendering using icons and Bootstrap colors.
    """

    def __init__(self, *args, **kwargs):
        default = kwargs.pop("default", "")
        visible = kwargs.pop("visible", True)
        if "attrs" not in kwargs:
            kwargs["attrs"] = {
                "td": {"class": "text-center"},
                "th": {"class": "text-center"},
            }
        super().__init__(*args, default=default, visible=visible, **kwargs)

    def render(self, value, record, bound_column):
        if not self._get_bool_value(record, value, bound_column):
            html = '<i class="fas fa-times text-danger"></i>'
        elif value is None:
            html = '<span class="text-muted">&mdash;</span>'
        else:
            html = '<i class="fas fa-check text-success"></i>'

        return mark_safe(html)

    def value(self, value):
        return str(value)


class ButtonsColumn(tables.TemplateColumn):
    """
    Renders buttons for an object, in a row of a table.
    """

    attrs = {"td": {"class": "text-right text-nowrap"}}
    # Note that braces are escaped to allow string formatting prior to template
    # rendering
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
    name = tables.Column(linkify=True)
    color = ColourColumn()
    actions = ButtonsColumn(Tag, buttons=("edit", "delete"))

    class Meta(BaseTable.Meta):
        model = Tag
        fields = ("pk", "name", "slug", "color", "items", "actions")
        default_columns = ("pk", "name", "color", "items", "actions")
