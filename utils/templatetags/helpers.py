from json import dumps as json_dumps
from markdown import markdown as md

from django import template
from django.utils.safestring import mark_safe


register = template.Library()


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
    Render text as GitHub-Flavored Markdown.
    """
    return mark_safe(md(value, extensions=["mdx_gfm"]))


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
