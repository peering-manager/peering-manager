import datetime
import json
import re
from pathlib import Path

import yaml
from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import date
from django.utils.html import escape, strip_tags
from django.utils.safestring import mark_safe
from markdown import markdown as md

from ..forms import TableConfigForm

register = template.Library()


@register.filter()
def boolean_as_icon(value):
    if value:
        icon, colour = "check", "success"
    else:
        icon, colour = "times", "danger"
    return mark_safe(f'<i class="fas fa-{icon} text-{colour}"></i>')


@register.filter()
def status_as_badge(value):
    """
    Renders a Bootstrap badge for a status field.
    """
    if not hasattr(value, "status"):
        return ""

    return mark_safe(
        f'<span class="badge badge-{value.get_status_colour()}">{value.get_status_display()}</span>'
    )


@register.filter()
def as_link(value):
    if not hasattr(value, "get_absolute_url"):
        return value
    return mark_safe(f'<a href="{value.get_absolute_url()}">{escape(value)}</a>')


@register.filter()
def render_bandwidth_speed(speed):
    """
    Renders speeds given in Mbps.
    """
    if not speed:
        return ""
    if speed >= 1000000 and speed % 1000000 == 0:
        return f"{int(speed / 1000000)} Tbps"
    if speed >= 1000 and speed % 1000 == 0:
        return f"{int(speed / 1000)} Gbps"
    if speed >= 1000:
        return f"{float(speed) / 1000} Gbps"
    return f"{speed} Mbps"


@register.filter()
def render_none(value):
    """
    Render a placeholder if a value is null or an empty string.
    """
    if value is None or value == "":
        return mark_safe('<span class="text-muted">&mdash;</span>')
    return as_link(value)


@register.filter()
def contains(value, arg):
    """
    Test whether a value contains any of a given set of strings.
    `arg` should be a comma-separated list of strings.
    """
    return any(s in value for s in arg.split(","))


@register.filter()
def notcontains(value, arg):
    """
    Test whether a value does not contain any of a given set of strings.
    `arg` should be a comma-separated list of strings.
    """
    return all(s not in value for s in arg.split(","))


@register.filter
def get_key(value, arg):
    return value.get(arg, None)


@register.filter(is_safe=True)
def markdown(value, escape_html=False):
    """
    Render text as Markdown.
    """
    # Strip HTML tags and render Markdown
    html = md(strip_tags(value), extensions=["fenced_code", "tables"])
    if escape_html:
        html = escape(html)
    return mark_safe(html)


@register.simple_tag()
def querystring(request, **kwargs):
    """
    Append or update the page number in a querystring.
    """
    querydict = request.GET.copy()

    for k, v in kwargs.items():
        if v is not None:
            querydict[k] = v
        elif k in querydict:
            querydict.pop(k)

    querystring = querydict.urlencode(safe="/")
    return "?" + querystring if querystring else ""


@register.filter("startswith")
def startswith(text, starts):
    """
    Template implementation of `str.startswith()`.
    """
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter()
def render_json(value):
    """
    Render a dictionary as formatted JSON.
    """
    return json.dumps(value, indent=4, sort_keys=True)


@register.filter()
def render_yaml(value):
    """
    Render a dictionary as formatted YAML.
    """
    return yaml.dump(
        json.loads(json.dumps(value)), explicit_start=True, explicit_end=False, indent=2
    )


@register.filter()
def title_with_uppers(value):
    """
    Render a title without touching to letter already being uppercased.
    """
    if not isinstance(value, str):
        value = str(value)
    return " ".join([word[0].upper() + word[1:] for word in value.split()])


@register.filter()
def meta(instance, attr):
    """
    Returns the specified `Meta` attribute of a model (Django does not allow that by
    default).
    """
    return getattr(instance._meta, attr, "")


@register.filter()
def content_type(instance):
    """
    Returns the `ContentType` for the given object.
    """
    return ContentType.objects.get_for_model(instance)


@register.filter()
def content_type_id(instance):
    """
    Return the `ContentType` ID for the given object.
    """
    content_type = ContentType.objects.get_for_model(instance)
    if content_type:
        return content_type.pk
    return None


@register.inclusion_tag("utils/templatetags/tag.html")
def tag(tag, url_name=None):
    """
    Render a tag and a URL to filter by it if the base URL is provided.
    """
    return {"tag": tag, "url_name": url_name}


@register.filter()
def foreground_colour(value):
    """
    Return black (#000000) or white (#ffffff) given a background colour in RRGGBB
    format.
    """
    value = value.lower().strip("#")
    if not re.match("^[0-9a-f]{6}$", value):
        return ""

    r, g, b = (int(value[c : c + 2], 16) for c in (0, 2, 4))
    if r * 0.299 + g * 0.587 + b * 0.114 > 186:
        return "#000000"
    return "#ffffff"


@register.filter()
def get_docs(model):
    """
    Render and return documentation for the given model.
    """
    path = Path(
        settings.DOCS_DIR,
        "models",
        model._meta.app_label,
        f"{model._meta.model_name}.md",
    )
    try:
        with path.open(encoding="utf-8") as docfile:
            content = docfile.read()
    except FileNotFoundError:
        return f"Unable to load documentation, file not found: {str(path)}"
    except OSError:
        return f"Unable to load documentation, error reading file: {str(path)}"

    return mark_safe(markdown(content))


@register.filter(expects_localtime=True)
def date_span(date_value):
    """
    Returns the date in a HTML span formatted as short date with a long date format as
    the title.
    """
    if not date_value:
        return ""

    if isinstance(date_value, str):
        date_value = (
            datetime.datetime.strptime(date_value, "%Y-%m-%d")
            .astimezone(tz=settings.TIME_ZONE)
            .date()
        )

    if type(date_value) is datetime.date:
        long = date(date_value, settings.DATE_FORMAT)
        short = date(date_value, settings.SHORT_DATE_FORMAT)
    else:
        long = date(date_value, settings.DATETIME_FORMAT)
        short = date(date_value, settings.SHORT_DATETIME_FORMAT)

    return mark_safe(f'<span title="{long}">{short}</span>')


@register.simple_tag(takes_context=True)
def missing_sessions(context, autonomous_system):
    if "context_as" not in context or not context["context_as"]:
        return False

    ix = autonomous_system.get_shared_internet_exchange_points(context["context_as"])
    for i in ix:
        if autonomous_system.get_missing_peering_sessions(context["context_as"], i):
            return True

    return False


@register.filter
def doc_version(version):
    if "-dev" in version:
        return "latest"
    return f"v{version}"


@register.inclusion_tag("helpers/table_config_form.html")
def table_config_form(table, table_name=None):
    return {
        "table_name": table_name or table.__class__.__name__,
        "form": TableConfigForm(table=table),
    }
