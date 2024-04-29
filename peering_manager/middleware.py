import uuid
from urllib import parse

from django.conf import settings
from django.db import ProgrammingError
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse

from extras.context_managers import change_logging
from utils.api import is_api_request, rest_api_server_error

from .views import handler_500

__all__ = ("CoreMiddleware",)


class CoreMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Assign a random unique ID to the request, used by change logging
        request.id = uuid.uuid4()

        # Enforce the LOGIN_REQUIRED config parameter.
        if settings.LOGIN_REQUIRED and not request.user.is_authenticated:
            if (
                not request.path_info.startswith(reverse("api-root"))
                and request.path_info != settings.LOGIN_URL
                and not request.path.startswith("/oidc/")
                and not request.path.startswith("/sso/")
            ):
                return HttpResponseRedirect(
                    f"{settings.LOGIN_URL}?next={parse.quote(request.get_full_path_info())}"
                )

        # Set last search path if the user just performed a search (query string not
        # empty), this variable will last all the session life time
        if (
            not is_api_request(request)
            and request.path_info != settings.LOGIN_URL
            and request.META["QUERY_STRING"]
        ):
            request.session["last_search"] = (
                f"{request.path_info}?{request.META['QUERY_STRING']}"
            )

        # Enable the change_logging context manager and process the request.
        with change_logging(request):
            response = self.get_response(request)

        # Attach the unique request ID as an HTTP header.
        response["X-Request-ID"] = request.id

        # If this is an API request, attach an HTTP header annotating the API version
        # (e.g. '1.8').
        if is_api_request(request):
            response["API-Version"] = settings.REST_FRAMEWORK_VERSION

        return response

    def process_exception(self, request, exception):
        # Ignore exception catching if debug mode is on
        if settings.DEBUG:
            return None

        # Lets Django handling 404
        if isinstance(exception, Http404):
            return None

        # Handle exceptions that occur from REST API requests
        if is_api_request(request):
            return rest_api_server_error(request)

        template = None
        if isinstance(exception, ProgrammingError):
            template = "errors/programming_error.html"
        elif isinstance(exception, ImportError):
            template = "errors/import_error.html"

        if template:
            return handler_500(request, template_name=template)

        return None
