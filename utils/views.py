import sys

from django.http import HttpResponseServerError
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import ERROR_500_TEMPLATE_NAME


@requires_csrf_token
def ServerError(request, template_name=ERROR_500_TEMPLATE_NAME):
    """
    Custom 500 handler to provide details when rendering 500.html.
    """
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseServerError(
            "<h1>Server Error (500)</h1>", content_type="text/html"
        )
    type_, error, _ = sys.exc_info()

    return HttpResponseServerError(
        template.render({"exception": str(type_), "error": error})
    )
