import logging
import uuid
from urllib import parse

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.middleware import (
    RemoteUserMiddleware as DjangoRemoteUserMiddleware,
)
from django.core.exceptions import ImproperlyConfigured
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
        if (
            settings.LOGIN_REQUIRED
            and not request.user.is_authenticated
            and not request.path_info.startswith(settings.AUTH_EXEMPT_PATHS)
        ):
            return HttpResponseRedirect(
                f"{settings.LOGIN_URL}?next={parse.quote(request.get_full_path_info())}"
            )

        # Set last search path if the user just performed a search (query string not
        # empty), this variable will last all the session life time
        if (
            not request.path_info.startswith(settings.AUTH_EXEMPT_PATHS)
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


class RemoteUserMiddleware(DjangoRemoteUserMiddleware):
    """
    Custom implementation of Django's RemoteUserMiddleware which allows for a user-configurable HTTP header name.
    """

    force_logout_if_no_header = False

    @property
    def header(self):
        return settings.REMOTE_AUTH_HEADER

    def process_request(self, request):
        logger = logging.getLogger(
            "peering.manager.authentication.RemoteUserMiddleware"
        )

        # Bypass middleware if remote authentication is not enabled
        if not settings.REMOTE_AUTH_ENABLED:
            return

        # AuthenticationMiddleware is required so that request.user exists
        if not hasattr(request, "user"):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the authentication middleware to be installed. Edit your MIDDLEWARE setting to insert 'django.contrib.auth.middleware.AuthenticationMiddleware' before the RemoteUserMiddleware class."
            )

        try:
            username = request.META[self.header]
        except KeyError:
            # If specified header doesn't exist then remove any existing authenticated
            # remote-user, or return (leaving request.user set to AnonymousUser by the
            # AuthenticationMiddleware)
            if self.force_logout_if_no_header and request.user.is_authenticated:
                self._remove_invalid_user(request)
            return

        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already persisted in
        # the session and we don't need to continue
        if request.user.is_authenticated:
            if request.user.get_username() == self.clean_username(username, request):
                return

            # An authenticated user is associated with the request, but it does not
            # match the authorized user in the header
            self._remove_invalid_user(request)

        # We are seeing this user for the first time in this session, attempt to
        # authenticate the user
        if settings.REMOTE_AUTH_GROUP_SYNC_ENABLED:
            logger.debug("trying to sync groups")
            user = auth.authenticate(
                request, remote_user=username, remote_groups=self._get_groups(request)
            )
        else:
            user = auth.authenticate(request, remote_user=username)

        if user:
            # User is valid
            # Update the user's profile if set by request headers
            if settings.REMOTE_AUTH_USER_FIRST_NAME in request.META:
                user.first_name = request.META[settings.REMOTE_AUTH_USER_FIRST_NAME]
            if settings.REMOTE_AUTH_USER_LAST_NAME in request.META:
                user.last_name = request.META[settings.REMOTE_AUTH_USER_LAST_NAME]
            if settings.REMOTE_AUTH_USER_EMAIL in request.META:
                user.email = request.META[settings.REMOTE_AUTH_USER_EMAIL]
            user.save()

            # Set request.user and persist user in the session by logging the user in
            request.user = user
            auth.login(request, user)

    def _get_groups(self, request):
        logger = logging.getLogger(
            "peering.manager.authentication.RemoteUserMiddleware"
        )

        groups_string = request.META.get(settings.REMOTE_AUTH_GROUP_HEADER, None)
        if groups_string:
            groups = groups_string.split(settings.REMOTE_AUTH_GROUP_SEPARATOR)
        else:
            groups = []
        logger.debug(f"groups are {groups}")
        return groups
