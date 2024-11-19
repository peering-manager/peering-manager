import platform
import sys

from django.conf import settings
from django.db import ProgrammingError
from django.http import HttpResponseServerError
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import ERROR_500_TEMPLATE_NAME

from utils.api import is_api_request, rest_api_server_error

__all__ = ("handler_500", "trigger_500")


@requires_csrf_token
def handler_500(request, template_name=ERROR_500_TEMPLATE_NAME):
    """
    Custom 500 handler to provide additional context when rendering 500.html.
    """
    if is_api_request(request):
        return rest_api_server_error(request)

    type_, error, _ = sys.exc_info()

    if isinstance(error, ProgrammingError):
        template_name = "errors/programming_error.html"
    elif isinstance(error, ImportError):
        template_name = "errors/import_error.html"

    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseServerError(
            "<h1>Server Error (500)</h1>", content_type="text/html"
        )

    return HttpResponseServerError(
        template.render(
            {
                "error": error,
                "exception": str(type_),
                "peering_manager_version": settings.VERSION,
                "python_version": platform.python_version(),
            }
        )
    )


def trigger_500(request):
    """
    Method to fake trigger a server error for test reporting.
    """
    raise Exception("Manually triggered error.")
