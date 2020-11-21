import threading
import uuid
from copy import deepcopy
from datetime import timedelta

from django.conf import settings
from django.db import ProgrammingError
from django.db.models.signals import post_save, pre_delete
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from redis.exceptions import RedisError

from webhooks.workers import enqueue_webhooks

from .enums import ObjectChangeAction
from .models import ObjectChange
from .views import ServerError

# For resources sharing
local_thread = threading.local()


def cache_changed_object(instance, **kwargs):
    """
    Add an object changed to the local thread and specify if it has been created or
    modified.
    """
    action = (
        ObjectChangeAction.CREATE if kwargs["created"] else ObjectChangeAction.UPDATE
    )

    # Cache the object to finish processing it once the response has completed
    local_thread.changed_objects.append((instance, action))


def cache_deleted_object(instance, **kwargs):
    """
    Record a deleted object as an object change.
    """
    copy = deepcopy(instance)
    local_thread.changed_objects.append((copy, ObjectChangeAction.DELETE))


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

        # Listen for objects being saved (created/updated) and deleted
        post_save.connect(cache_changed_object, dispatch_uid="log_object_being_changed")
        pre_delete.connect(
            cache_deleted_object, dispatch_uid="log_object_being_deleted"
        )

        # Process the request
        response = self.get_response(request)

        # Nothing to do as there are no changes to process
        if not local_thread.changed_objects:
            return response

        # Stop listening for object changes
        post_save.disconnect(
            cache_changed_object, dispatch_uid="log_object_being_changed"
        )
        pre_delete.disconnect(
            cache_deleted_object, dispatch_uid="log_object_being_deleted"
        )

        # Record change for each object that need to be tracked
        has_redis_failed = False
        for changed_object, action in local_thread.changed_objects:
            if hasattr(changed_object, "log_change"):
                changed_object.log_change(request.user, request.id, action)

            try:
                enqueue_webhooks(changed_object, request.user, request.id, action)
            except RedisError as e:
                if not has_redis_failed:
                    messages.error(
                        request,
                        f"An error has occured while processing webhooks for this request. Check that the Redis service is running and reachable. The full error details were: {e}",
                    )
                    has_redis_failed = True

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
            if (
                not request.path_info.startswith(reverse("api-root"))
                and request.path_info != settings.LOGIN_URL
            ):
                return HttpResponseRedirect(
                    f"{settings.LOGIN_URL}?next={request.path_info}"
                )

        return self.get_response(request)
