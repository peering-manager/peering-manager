import django_tables2 as tables
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import RelatedField
from django.utils.safestring import mark_safe

from .functions import content_type_identifier, content_type_name
from .paginators import EnhancedPaginator, get_paginate_count


def linkify_phone(value):
    """
    Returns a user friendly clickable phone string.
    """
    if value is None:
        return None
    return f"tel:{value}"


def paginate_table(table, request):
    """
    Paginates a table given a request context.
    """
    paginate = {
        "paginator_class": EnhancedPaginator,
        "per_page": get_paginate_count(request),
    }
    tables.RequestConfig(request, paginate).configure(table)


class BaseTable(tables.Table):
    """
    Default table for object lists
    """

    exempt_columns = ("pk", "actions")

    class Meta:
        attrs = {"class": "table table-sm table-hover table-headings"}

    def __init__(
        self, *args, user=None, extra_columns=None, no_actions=False, **kwargs
    ):
        super().__init__(*args, extra_columns=extra_columns, **kwargs)

        # Set default empty_text if none was provided
        if self.empty_text is None:
            self.empty_text = f"No {self._meta.model._meta.verbose_name_plural} found."

        # Determine the table columns to display by checking the following:
        #   1. User's preferences for the table
        #   2. Meta.default_columns
        #   3. Meta.fields
        selected_columns = None
        if user is not None and not isinstance(user, AnonymousUser):
            selected_columns = user.preferences.get(
                f"tables.{self.__class__.__name__}.columns".lower()
            )
        if not selected_columns:
            selected_columns = getattr(self.Meta, "default_columns", self.Meta.fields)

        # Hide non-selected columns which are not exempt
        for column in self.columns:
            if column.name not in [*selected_columns, *self.exempt_columns]:
                self.columns.hide(column.name)

        # Rearrange the sequence to list selected columns first, followed by all
        # remaining columns
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
            if not no_actions:
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
        super().__init__(template_code=template_code, *args, orderable=False, **kwargs)

        self.extra_context.update(
            {"buttons": buttons, "return_url_extra": return_url_extra}
        )

    def header(self):
        return ""


class ChoiceFieldColumn(tables.Column):
    """
    Renders a model's static choice field with its value from `get_*_display()` as a
    coloured badge. The background colour is infered by `get_*_colour()`.
    """

    DEFAULT_BG_COLOUR = "secondary"

    def render(self, record, bound_column, value):
        if value in self.empty_values:
            return self.default

        try:
            bg_colour = getattr(record, f"get_{bound_column.name}_colour")()
        except AttributeError:
            bg_colour = self.DEFAULT_BG_COLOUR
        return mark_safe(f'<span class="badge badge-{bg_colour}">{value}</span>')

    def value(self, value):
        return value


class ColourColumn(tables.Column):
    """
    Displays a coloured block.
    """

    def render(self, value):
        return mark_safe(
            f'<span class="label color-block" style="background-color: #{value}">&nbsp;</span>'
        )


class ContentTypeColumn(tables.Column):
    """
    Display a ContentType instance.
    """

    def render(self, value):
        if value is None:
            return None
        return content_type_name(value)

    def value(self, value):
        if value is None:
            return None
        return content_type_identifier(value)


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
