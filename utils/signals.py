import random
from datetime import timedelta

from cacheops.signals import cache_invalidated, cache_read
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.utils import timezone
from django_prometheus.models import model_deletes, model_inserts, model_updates
from prometheus_client import Counter

from webhooks.workers import enqueue_webhooks

from .enums import ObjectChangeAction
from .models import ObjectChange


def _handle_changed_object(request, sender, instance, **kwargs):
    """
    Fires when an object is created or updated.
    """
    # Queue the object for processing once the request completes
    if kwargs.get("created"):
        action = ObjectChangeAction.CREATE
    elif "created" in kwargs:
        action = ObjectChangeAction.UPDATE
    elif kwargs.get("action") in ["post_add", "post_remove"] and kwargs["pk_set"]:
        # m2m_changed with objects added or removed
        action = ObjectChangeAction.UPDATE
    else:
        return

    # Record an ObjectChange if applicable
    if hasattr(instance, "get_change"):
        change = instance.get_change(action)
        change.user = request.user
        change.request_id = request.id
        change.save()

    # Enqueue webhooks
    enqueue_webhooks(instance, request.user, request.id, action)

    # Increment metric counters
    if action == ObjectChangeAction.CREATE:
        model_inserts.labels(instance._meta.model_name).inc()
    elif action == ObjectChangeAction.UPDATE:
        model_updates.labels(instance._meta.model_name).inc()

    # Housekeeping: 0.1% chance of clearing out expired ObjectChanges
    if settings.CHANGELOG_RETENTION and random.randint(1, 1000) == 1:
        date_limit = timezone.now() - timedelta(days=settings.CHANGELOG_RETENTION)
        ObjectChange.objects.filter(time__lt=date_limit)._raw_delete(
            using=DEFAULT_DB_ALIAS
        )


def _handle_deleted_object(request, sender, instance, **kwargs):
    """
    Fires when an object is deleted.
    """
    # Record an ObjectChange if applicable
    if hasattr(instance, "get_change"):
        change = instance.get_change(ObjectChangeAction.DELETE)
        change.user = request.user
        change.request_id = request.id
        change.save()

    # Enqueue webhooks
    enqueue_webhooks(instance, request.user, request.id, ObjectChangeAction.DELETE)

    # Increment metric counters
    model_deletes.labels(instance._meta.model_name).inc()


cacheops_cache_hit = Counter("cacheops_cache_hit", "Number of cache hits")
cacheops_cache_miss = Counter("cacheops_cache_miss", "Number of cache misses")
cacheops_cache_invalidated = Counter(
    "cacheops_cache_invalidated", "Number of cache invalidations"
)


def cache_read_collector(sender, func, hit, **kwargs):
    if hit:
        cacheops_cache_hit.inc()
    else:
        cacheops_cache_miss.inc()


def cache_invalidated_collector(sender, obj_dict, **kwargs):
    cacheops_cache_invalidated.inc()


cache_read.connect(cache_read_collector)
cache_invalidated.connect(cache_invalidated_collector)
