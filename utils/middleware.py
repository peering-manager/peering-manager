import uuid

from django.conf import settings
from django.db import ProgrammingError
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse

from utils.api import is_api_request, rest_api_server_error
from utils.context_managers import change_logging
from utils.views import ServerError


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

        # Handle exceptions that occur from REST API requests
        if is_api_request(request):
            return rest_api_server_error(request)

        template = None
        if isinstance(exception, ProgrammingError):
            template = "errors/programming_error.html"
        elif isinstance(exception, ImportError):
            template = "errors/import_error.html"

        if template:
            return ServerError(request, template_name=template)


class ObjectChangeMiddleware(object):
    """
    Create ObjectChange objects to reflect modifications done to objects.

    This middleware aims to automatically record object changes without having to
    write code for this every time a modification is supposed to happen. This will
    help to keep things simple and maintainable.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Assign a random unique ID to the request
        # This will be used to associate multiple object changes made during the same
        # request
        request.id = uuid.uuid4()

        # Process the request with change logging enabled
        with change_logging(request):
            response = self.get_response(request)

        return response


class RequireLoginMiddleware(object):
    """
    Redirect all non-authenticated user to the login page if the LOGIN_REQUIRED
    setting has been set to true.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.LOGIN_REQUIRED and not request.user.is_authenticated:
            if (
                not request.path_info.startswith(reverse("api-root"))
                and request.path_info != settings.LOGIN_URL
            ):
                return HttpResponseRedirect(
                    f"{settings.LOGIN_URL}?next={request.path_info}"
                )

        return self.get_response(request)
