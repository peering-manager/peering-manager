import sys
import threading
import uuid

from datetime import timedelta

from django.db import ProgrammingError
from django.db.models.signals import post_delete, post_save
from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.utils import timezone
from django.utils.functional import curry

from .views import ServerError
from utils.constants import *
from utils.models import ObjectChange


# For resources sharing
local_thread = threading.local()


def cache_changed_object(instance, **kwargs):
    """
    Add an object changed to the local thread and specify if it has been created or
    modified.
    """
    action = (
        OBJECT_CHANGE_ACTION_CREATE
        if kwargs["created"]
        else OBJECT_CHANGE_ACTION_UPDATE
    )

    # Cache the object to finish processing it once the response has completed
    local_thread.changed_objects.append((instance, action))


def cache_deleted_object(request, instance, **kwargs):
    """
    Record a deleted object as an object change.
    """
    if hasattr(instance, "log_change"):
        instance.log_change(request.user, request.id, OBJECT_CHANGE_ACTION_DELETE)


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
        # Prepare to collect objects that have been changed
        local_thread.changed_objects = []

        # Assign an ID to the given request in case we have to handle multiple objects
        request.id = uuid.uuid4()

        # Listen for objects being saved (created/updated)
        post_save.connect(cache_changed_object, dispatch_uid="log_object_being_changed")

        # Curry context to inform the function, to be called on delete, about the
        # request's context and listen for objects being deleted
        cache_deleted_object_with_context = curry(cache_deleted_object, request)
        post_delete.connect(
            cache_deleted_object_with_context, dispatch_uid="log_object_being_deleted"
        )

        # Process the request
        response = self.get_response(request)

        # Record change for each object that need to be tracked
        for changed_object, action in local_thread.changed_objects:
            if hasattr(changed_object, "log_change"):
                changed_object.log_change(request.user, request.id, action)

        # Cleanup object changes that are too old (based on changelog retention)
        if local_thread.changed_objects and settings.CHANGELOG_RETENTION:
            date_limit = timezone.now() - timedelta(days=settings.CHANGELOG_RETENTION)
            ObjectChange.objects.filter(time__lt=date_limit).delete()

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
            if request.path_info != settings.LOGIN_URL:
                return HttpResponseRedirect(
                    "{}?next={}".format(settings.LOGIN_URL, request.path_info)
                )

        return self.get_response(request)
