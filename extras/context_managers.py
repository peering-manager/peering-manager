from contextlib import contextmanager

from peering_manager.context import current_request, webhooks_queue

from .webhooks import flush_webhooks


@contextmanager
def change_logging(request):
    """
    Enables change logging by connecting the appropriate signals to their receivers
    before code is run, and disconnecting them afterward.
    """
    current_request.set(request)
    webhooks_queue.set([])

    yield

    # Flush queued webhooks to RQ
    flush_webhooks(webhooks_queue.get())

    # Clear context vars
    current_request.set(None)
    webhooks_queue.set([])
