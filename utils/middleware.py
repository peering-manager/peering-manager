import sys

from django.db import ProgrammingError
from django.conf import settings
from django.http import Http404, HttpResponseRedirect

from .views import ServerError


class ExceptionCatchingMiddleware(object):
    """
    Catch some exceptions which can give clues about some issues or
    instructions to the end-user.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # Ignore exception catching if debug mode is on
        if settings.DEBUG:
            return

        # Lets Django handling 404
        if isinstance(exception, Http404):
            return

        template = None
        if isinstance(exception, ProgrammingError):
            template = "errors/programming_error.html"
        elif isinstance(exception, ImportError):
            template = "errors/import_error.html"

        if template:
            return ServerError(request, template_name=template)


class RequireLoginMiddleware(object):
    """
    Redirect all non-authenticated user to the login page if the LOGIN_REQUIRED
    setting has been set to true.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.LOGIN_REQUIRED and not request.user.is_authenticated:
            if request.path_info != settings.LOGIN_URL:
                return HttpResponseRedirect(
                    "{}?next={}".format(settings.LOGIN_URL, request.path_info)
                )

        return self.get_response(request)
