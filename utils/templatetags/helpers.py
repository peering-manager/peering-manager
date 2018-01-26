from __future__ import unicode_literals

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
    return any(s in value for s in arg.split(','))


@register.filter()
def example_choices(field, number=3):
    examples = []

    for key, label in field.choices:
        # We have reached the maximum number of examples
        if len(examples) == number:
            examples.append('etc.')
            break

        # No key, weird...
        if not key:
            continue

        examples.append(label)

    return ', '.join(examples) or None


@register.filter(is_safe=True)
def markdown(value):
    """
    Render text as GitHub-Flavored Markdown.
    """
    return mark_safe(md(value, extensions=['mdx_gfm']))


@register.filter()
def notcontains(value, arg):
    """
    Test whether a value does not contain any of a given set of strings.
    `arg` should be a comma-separated list of strings.
    """
    for s in arg.split(','):
        if s in value:
            return False
    return True


@register.simple_tag()
def querystring(request, **kwargs):
    """
    Append or update the page number in a querystring.
    """
    querydict = request.GET.copy()
    for key, value in kwargs.items():
        if value is not None:
            querydict[key] = value
        elif key in querydict:
            querydict.pop(key)

    querystring = querydict.urlencode()
    if querystring:
        return '?' + querystring

    return ''
