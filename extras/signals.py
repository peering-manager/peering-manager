import logging

from django.dispatch import Signal, receiver

from peering_manager.context import webhooks_queue

# Define a custom signal that can be sent to clear any queued webhooks
clear_webhooks = Signal()


@receiver(clear_webhooks)
def clear_webhook_queue(sender, **kwargs):
    """
    Deletes any queued webhooks (e.g. because of an aborted bulk transaction).
    """
    logging.getLogger("peering_manager.extras.webhooks").info(
        f"clearing {len(webhooks_queue.get())} queued webhooks ({sender})"
    )
    webhooks_queue.set([])
