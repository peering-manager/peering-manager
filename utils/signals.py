import logging
import random
from datetime import timedelta

from cacheops.signals import cache_invalidated, cache_read
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import DEFAULT_DB_ALIAS
from django.dispatch import Signal
from django.utils import timezone
from django_prometheus.models import model_deletes, model_inserts, model_updates
from prometheus_client import Counter

from extras.webhooks import enqueue_object, get_snapshots, serialize_for_webhook
from peering_manager import thread_locals
from peering_manager.request_context import get_request
from utils.enums import ObjectChangeAction
from utils.models import ObjectChange

# Define a custom signal that can be sent to clear any queued webhooks
clear_webhooks = Signal()


def handle_changed_object(sender, instance, **kwargs):
    """
    Fires when an object is created or updated.
    """
    # Ignore object without the right method
    if not hasattr(instance, "to_objectchange"):
        return

    request = get_request()
    m2m_changed = False

    def is_same_object(instance, webhook_data):
        return (
            instance.pk == webhook_data["object_id"]
            and request.id == webhook_data["request_id"]
        )

    # Queue the object for processing once the request completes
    if kwargs.get("created"):
        action = ObjectChangeAction.CREATE
    elif "created" in kwargs:
        action = ObjectChangeAction.UPDATE
    elif kwargs.get("action") in ["post_add", "post_remove"] and kwargs["pk_set"]:
        # m2m_changed with objects added or removed
        m2m_changed = True
        action = ObjectChangeAction.UPDATE
    else:
        return

    if m2m_changed:
        ObjectChange.objects.filter(
            changed_object_type=ContentType.objects.get_for_model(instance),
            changed_object_id=instance.pk,
            request_id=request.id,
        ).update(postchange_data=instance.to_objectchange(action).postchange_data)
    else:
        # Record an object change
        change = instance.to_objectchange(action)
        change.user = request.user
        change.request_id = request.id
        change.save()

    # If this is an M2M change, update the previously queued webhook (from post_save)
    webhook_queue = thread_locals.webhook_queue
    if m2m_changed and webhook_queue and is_same_object(instance, webhook_queue[-1]):
        instance.refresh_from_db()  # Ensure that we're working with fresh M2M assignments
        webhook_queue[-1]["data"] = serialize_for_webhook(instance)
        webhook_queue[-1]["snapshots"]["postchange"] = get_snapshots(instance, action)[
            "postchange"
        ]
    else:
        enqueue_object(webhook_queue, instance, request.user, request.id, action)

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


def handle_deleted_object(sender, instance, **kwargs):
    """
    Fires when an object is deleted.
    """
    # Ignore object without the right method
    if not hasattr(instance, "to_objectchange"):
        return

    request = get_request()

    # Record an object change
    change = instance.to_objectchange(ObjectChangeAction.DELETE)
    change.user = request.user
    change.request_id = request.id
    change.save()

    # Enqueue webhooks
    webhook_queue = thread_locals.webhook_queue
    enqueue_object(
        webhook_queue, instance, request.user, request.id, ObjectChangeAction.DELETE
    )

    # Increment metric counters
    model_deletes.labels(instance._meta.model_name).inc()


def clear_webhook_queue(sender, **kwargs):
    """
    Deletes any queued webhooks (e.g. because of an aborted bulk transaction).
    """
    logger = logging.getLogger("webhooks")
    webhook_queue = thread_locals.webhook_queue

    logger.info(f"clearing {len(webhook_queue)} queued webhooks ({sender})")
    webhook_queue.clear()


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
