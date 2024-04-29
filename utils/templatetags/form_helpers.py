from django import template

__all__ = ("getfield", "render_errors", "render_field", "render_form", "widget_type")

register = template.Library()


@register.filter()
def getfield(form, fieldname):
    """
    Return the specified bound field of a Form.
    """
    try:
        return form[fieldname]
    except KeyError:
        return None


@register.inclusion_tag("form_helpers/render_errors.html")
def render_errors(form):
    """
    Render form errors, if they exist.
    """
    return {"form": form}


@register.inclusion_tag("form_helpers/render_field.html")
def render_field(field, bulk_nullable=False, label=None):
    """
    Render a single form field from template
    """
    return {
        "field": field,
        "label": label or field.label,
        "bulk_nullable": bulk_nullable,
    }


@register.inclusion_tag("form_helpers/render_form.html")
def render_form(form):
    """
    Render a form by rendering all fields.
    """
    return {"form": form}


@register.filter(name="widget_type")
def widget_type(field):
    """
    Return the widget type
    """
    if hasattr(field, "widget"):
        return field.widget.__class__.__name__.lower()
    if hasattr(field, "field"):
        return field.field.widget.__class__.__name__.lower()
    return None
