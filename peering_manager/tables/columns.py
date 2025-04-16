import zoneinfo
from dataclasses import dataclass
from urllib.parse import quote

import django_tables2 as tables
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.forms import DateTimeField
from django.template import Context, Template
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_tables2.columns import library

from utils.functions import content_type_identifier, content_type_name, get_viewname

__all__ = (
    "ActionsColumn",
    "BooleanColumn",
    "ChoiceFieldColumn",
    "ColourColumn",
    "ContentTypeColumn",
    "ContentTypesColumn",
    "DateTimeColumn",
    "LinkedCountColumn",
    "MarkdownColumn",
    "SelectColumn",
    "TagColumn",
    "ToggleColumn",
)


@dataclass
class ActionsItem:
    title: str
    icon: str
    permission: str = None
    css_class: str = "secondary"


class ActionsColumn(tables.Column):
    """
    A dropdown menu which provides edit, delete, and changelog links for an object.
    Can optionally include additional buttons rendered from a template string.

    The `actions` parameter is an ordered list of dropdown menu items to include.

    The `extra_buttons` parameter is a Django template string which renders additional
    buttons preceding the actions dropdown.

    When `split_actions` is set to `True`, it converts the actions dropdown menu into
    a split button with first action as the direct button link and icon (default:
    `True`).
    """

    attrs = {"td": {"class": "text-end text-nowrap"}}
    empty_values = ()
    actions = {
        "edit": ActionsItem("Edit", "edit", "change", "warning"),
        "delete": ActionsItem("Delete", "trash", "delete", "danger"),
        "changelog": ActionsItem("Changelog", "history"),
    }

    def __init__(
        self,
        *args,
        actions=("edit", "delete", "changelog"),
        extra_buttons="",
        split_actions=True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.extra_buttons = extra_buttons
        self.split_actions = split_actions

        # Determine which actions to enable
        self.actions = {name: self.actions[name] for name in actions}

    def filter_actions(self, user, model):
        """Remove actions that a user cannot perform."""
        filtered = {}

        for action, attrs in self.actions.items():
            permission = (
                f"{model._meta.app_label}.{attrs.permission}_{model._meta.model_name}"
            )
            if attrs.permission is None or user.has_perm(permission):
                filtered[action] = attrs

        return filtered

    def header(self):
        return ""

    def render(self, record, table, **kwargs):
        # Skip dummy records (no PK) or those with no actions
        if not getattr(record, "pk", None) or not self.actions:
            return ""

        model = table.Meta.model
        if request := getattr(table, "context", {}).get("request"):
            return_url = request.GET.get("return_url", request.get_full_path())
            url_appendix = f"?return_url={quote(return_url)}"
        else:
            url_appendix = ""

        html = ""

        # Compile actions menu
        button = None
        dropdown_class = "secondary"
        dropdown_links = []
        user = getattr(request, "user", AnonymousUser())
        for idx, (action, attrs) in enumerate(self.filter_actions(user, model).items()):
            url = reverse(get_viewname(model, action), kwargs={"pk": record.pk})

            # Render a separate button if:
            # a) only one action exists, or
            # b) if split_actions is True
            if len(self.actions) == 1 or (self.split_actions and idx == 0):
                dropdown_class = attrs.css_class
                button = f'<a class="btn btn-sm btn-{attrs.css_class}" href="{url}{url_appendix}" type="button"><i class="fa-fw fa-solid fa-{attrs.icon}"></i></a>'
            # Add dropdown menu items
            else:
                dropdown_links.append(
                    f'<li><a class="dropdown-item" href="{url}{url_appendix}"><i class="fa-fw fa-solid fa-{attrs.icon}"></i> {attrs.title}</a></li>'
                )

        # Create the actions dropdown menu
        if button and dropdown_links:
            html += (
                f'<span class="btn-group">'
                f"  {button}"
                f'  <a class="btn btn-sm btn-{dropdown_class} dropdown-toggle dropdown-toggle-split" type="button" data-bs-toggle="dropdown" style="padding-left: 2px">'
                f'  <span class="sr-only">Toggle Dropdown</span></a>'
                f'  <ul class="dropdown-menu">{"".join(dropdown_links)}</ul>'
                f"</span>"
            )
        elif button:
            html += button
        elif dropdown_links:
            html += (
                f'<span class="btn-group dropdown">'
                f'  <a class="btn btn-sm btn-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">'
                f'  <span class="sr-only">Toggle Dropdown</span></a>'
                f'  <ul class="dropdown-menu">{"".join(dropdown_links)}</ul>'
                f"</span>"
            )

        # Render any extra buttons from template code
        if self.extra_buttons:
            template = Template(self.extra_buttons)
            context = getattr(table, "context", Context())
            context.update({"record": record})
            html = template.render(context) + html

        return mark_safe(html)


class BooleanColumn(tables.BooleanColumn):
    """
    Simple column customising boolean value rendering using icons and Bootstrap colors.
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
            html = '<i class="fa-fw fa-solid fa-times text-danger"></i>'
        elif value is None:
            html = '<span class="text-muted">&mdash;</span>'
        else:
            html = '<i class="fa-fw fa-solid fa-check text-success"></i>'

        return mark_safe(html)

    def value(self, value):
        return str(value)


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
        return mark_safe(f'<span class="badge text-bg-{bg_colour}">{value}</span>')

    def value(self, value):
        return value


class ColourColumn(tables.Column):
    """
    Displays a coloured block.
    """

    def render(self, value):
        return mark_safe(
            f'<span class="label colour-block" style="background-color: #{value}">&nbsp;</span>'
        )


class ContentTypeColumn(tables.Column):
    """
    Display a ContentType instance.
    """

    def render(self, value):
        if value is None:
            return None
        return content_type_name(value, include_app=False)

    def value(self, value):
        if value is None:
            return None
        return content_type_identifier(value)


class ContentTypesColumn(tables.ManyToManyColumn):
    """
    Display a list of ContentType instances.
    """

    def __init__(self, separator=None, *args, **kwargs):
        # Use a line break as the default separator
        if separator is None:
            separator = mark_safe("<br />")
        super().__init__(*args, separator=separator, **kwargs)

    def transform(self, obj):
        return content_type_name(obj, include_app=False)

    def value(self, value):
        return ",".join([content_type_identifier(ct) for ct in self.filter(value)])


@library.register
class DateTimeColumn(tables.Column):
    """
    Render a datetime.datetime in ISO 8601 format.
    """

    def __init__(self, *args, timespec="seconds", **kwargs):
        self.timespec = timespec
        super().__init__(*args, **kwargs)

    def render(self, value):
        if value:
            current_tz = zoneinfo.ZoneInfo(settings.TIME_ZONE)
            value = value.astimezone(current_tz)
            return f"{value.date().isoformat()} {value.time().isoformat(timespec=self.timespec)}"
        return None

    def value(self, value):
        if value:
            return value.isoformat()
        return None

    @classmethod
    def from_field(cls, field, **kwargs):
        if isinstance(field, DateTimeField):
            return cls(**kwargs)
        return None


class LinkedCountColumn(tables.Column):
    """
    Render a count of related objects linked to a filtered URL.

    :param viewname: The view name to use for URL resolution
    :param view_kwargs: Additional kwargs to pass for URL resolution (optional)
    :param url_params: A dict of query parameters to append to the URL (e.g. ?foo=bar) (optional)
    """

    def __init__(
        self, viewname, *args, view_kwargs=None, url_params=None, default=0, **kwargs
    ):
        self.viewname = viewname
        self.view_kwargs = view_kwargs or {}
        self.url_params = url_params
        super().__init__(*args, default=default, **kwargs)

    def render(self, record, value):
        # Use a PK for reversing the URL
        if self.view_kwargs.get("pk", False):
            self.view_kwargs["pk"] = record.pk
        if value:
            url = reverse(self.viewname, kwargs=self.view_kwargs)
            if self.url_params:
                url += "?" + "&".join(
                    [
                        f"{k}={getattr(record, v) or settings.FILTERS_NULL_CHOICE_VALUE}"
                        for k, v in self.url_params.items()
                    ]
                )
            return mark_safe(f'<a href="{url}">{value}</a>')
        return value

    def value(self, value):
        return value


class MarkdownColumn(tables.TemplateColumn):
    """
    Render a Markdown string as a column.
    """

    template_code = """
    {% load helpers %}
    {% if value %}
    {{ value|markdown }}
    {% else %}
    &mdash;
    {% endif %}
    """

    def __init__(self, **kwargs):
        super().__init__(template_code=self.template_code, **kwargs)

    def value(self, value):
        return value


class SelectColumn(tables.CheckBoxColumn):
    def __init__(self, *args, **kwargs):
        default = kwargs.pop("default", "")
        visible = kwargs.pop("visible", False)
        if "attrs" not in kwargs:
            kwargs["attrs"] = {
                "th": {"class": "w-1", "aria-label": "Select all"},
                "td": {"class": "w-1"},
                "input": {"class": "form-check-input"},
            }

        super().__init__(*args, default=default, visible=visible, **kwargs)

    @property
    def header(self):
        return mark_safe(
            '<input type="checkbox" class="toggle form-check-input" title="Select all" />'
        )


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


class ToggleColumn(tables.CheckBoxColumn):
    """
    Extend CheckBoxColumn to add a "toggle all" checkbox in the column header.
    """

    def __init__(self, *args, **kwargs):
        default = kwargs.pop("default", "")
        visible = kwargs.pop("visible", False)
        if "attrs" not in kwargs:
            kwargs["attrs"] = {
                # "td": {"class": "min-width"},
                # "input": {"class": "form-check-input"},
            }
        super().__init__(*args, default=default, visible=visible, **kwargs)

    @property
    def header(self):
        return mark_safe('<input type="checkbox" class="toggle" title="Toggle All" />')
