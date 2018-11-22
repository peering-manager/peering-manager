from __future__ import unicode_literals

from django import template

register = template.Library()


@register.inclusion_tag('utils/render_field.html')
def render_field(field, bulk_nullable=False):
    """
    Render a single form field from template.
    """
    return {
        'field': field,
        'bulk_nullable': bulk_nullable,
    }


@register.inclusion_tag('utils/render_form.html')
def render_form(form):
    """
    Render a form by rendering all fields.
    """
    return {
        'form': form,
    }


@register.filter(name='widget_type')
def widget_type(field):
    """
    Return the widget type
    """
    if hasattr(field, 'widget'):
        return field.widget.__class__.__name__.lower()
    elif hasattr(field, 'field'):
        return field.field.widget.__class__.__name__.lower()
    else:
        return None
