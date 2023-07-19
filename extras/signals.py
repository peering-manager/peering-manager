import logging

from cacheops.signals import cache_invalidated, cache_read
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import Signal, receiver
from django_prometheus.models import model_deletes, model_inserts, model_updates
from prometheus_client import Counter

from peering_manager.context import current_request, webhooks_queue

from .enums import ObjectChangeAction
from .models import ObjectChange
from .webhooks import enqueue_object, get_snapshots, serialize_for_webhook

# Define a custom signal that can be sent to clear any queued webhooks
clear_webhooks = Signal()


def is_same_object(instance, webhook_data, request_id):
    """
    Compare the given instance to the most recent queued webhook object, returning True
    if they match. This check is used to avoid creating duplicate webhook entries.
    """
    return (
        instance.pk == webhook_data["object_id"]
        and request_id == webhook_data["request_id"]
    )


@receiver((post_save, m2m_changed))
def handle_changed_object(sender, instance, **kwargs):
    """
    Fires when an object is created or updated.
    """
    m2m_changed = False

    # Ignore object without the right method
    if not hasattr(instance, "to_objectchange"):
        return

    # Get the current request, or bail if not set
    request = current_request.get()
    if request is None:
        return

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
    queue = webhooks_queue.get()
    if m2m_changed and queue and is_same_object(instance, queue[-1], request.id):
        instance.refresh_from_db()  # Ensure that we're working with fresh M2M assignments
        queue[-1]["data"] = serialize_for_webhook(instance)
        queue[-1]["snapshots"]["postchange"] = get_snapshots(instance, action)[
            "postchange"
        ]
    else:
        enqueue_object(queue, instance, request.user, request.id, action)
    webhooks_queue.set(queue)

    # Increment metric counters
    if action == ObjectChangeAction.CREATE:
        model_inserts.labels(instance._meta.model_name).inc()
    elif action == ObjectChangeAction.UPDATE:
        model_updates.labels(instance._meta.model_name).inc()


@receiver(pre_delete)
def handle_deleted_object(sender, instance, **kwargs):
    """
    Fires when an object is deleted.
    """
    # Ignore object without the right method
    if not hasattr(instance, "to_objectchange"):
        return

    # Get the current request, or bail if not set
    request = current_request.get()
    if request is None:
        return

    # Record an object change
    change = instance.to_objectchange(ObjectChangeAction.DELETE)
    change.user = request.user
    change.request_id = request.id
    change.save()

    # Enqueue webhooks
    queue = webhooks_queue.get()
    enqueue_object(queue, instance, request.user, request.id, ObjectChangeAction.DELETE)
    webhooks_queue.set(queue)

    # Increment metric counters
    model_deletes.labels(instance._meta.model_name).inc()


@receiver(clear_webhooks)
def clear_webhook_queue(sender, **kwargs):
    """
    Deletes any queued webhooks (e.g. because of an aborted bulk transaction).
    """
    logging.getLogger("peering_manager.extras.webhooks").info(
        f"clearing {len(webhooks_queue.get())} queued webhooks ({sender})"
    )
    webhooks_queue.set([])


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
