import re

from json import dumps as json_dumps
from markdown import markdown as md

from django import template
from django.conf import settings
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter()
def boolean_as_icon(value):
    html = '<i class="fas fa-check text-success"></i>'
    if not value:
        html = '<i class="fas fa-times text-danger"></i>'

    return mark_safe(html)


@register.filter()
def as_link(value):
    return mark_safe('<a href="{}">{}</a>'.format(value.get_absolute_url(), value))


@register.filter()
def contains(value, arg):
    """
    Test whether a value contains any of a given set of strings.
    `arg` should be a comma-separated list of strings.
    """
    return any(s in value for s in arg.split(","))


@register.filter(is_safe=True)
def markdown(value):
    """
    Render text as Markdown.
    """
    # Strip HTML tags and render Markdown
    html = md(strip_tags(value), extensions=["fenced_code", "tables"])
    return mark_safe(html)


@register.filter()
def notcontains(value, arg):
    """
    Test whether a value does not contain any of a given set of strings.
    `arg` should be a comma-separated list of strings.
    """
    for s in arg.split(","):
        if s in value:
            return False
    return True


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


@register.filter()
def render_json(value):
    """
    Render a dictionary as formatted JSON.
    """
    return json_dumps(value, indent=4, sort_keys=True)


@register.filter()
def title_with_uppers(value):
    """
    Render a title without touching to letter already being uppercased.
    """
    if not isinstance(value, str):
        value = str(value)
    return " ".join([word[0].upper() + word[1:] for word in value.split()])


@register.inclusion_tag("utils/templatetags/tag.html")
def tag(tag, url_name=None):
    """
    Render a tag and a URL to filter by it if the base URL is provided.
    """
    return {"tag": tag, "url_name": url_name}


@register.filter()
def foreground_color(value):
    """
    Return black (#000000) or white (#ffffff) given a background color in RRGGBB format.
    """
    value = value.lower().strip("#")
    if not re.match("^[0-9a-f]{6}$", value):
        return ""

    r, g, b = [int(value[c : c + 2], 16) for c in (0, 2, 4)]
    if r * 0.299 + g * 0.587 + b * 0.114 > 186:
        return "#000000"
    else:
        return "#ffffff"


@register.filter()
def get_docs(model):
    """
    Render and return documentation for the given model.
    """
    path = f"{settings.DOCS_DIR}/models/{model._meta.app_label}/{model._meta.model_name}.md"
    try:
        with open(path, encoding="utf-8") as docfile:
            content = docfile.read()
    except FileNotFoundError:
        return f"Unable to load documentation, file not found: {path}"
    except IOError:
        return f"Unable to load documentation, error reading file: {path}"

    return mark_safe(markdown(content))


@register.filter()
def user_context_asn(request):
    return request.user.preferences.get("context.asn")
