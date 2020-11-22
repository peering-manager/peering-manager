from contextlib import contextmanager

from django.db.models.signals import m2m_changed, post_save, pre_delete

from utils.functions import curry
from utils.signals import _handle_changed_object, _handle_deleted_object


@contextmanager
def change_logging(request):
    """
    Enables change logging by connecting the appropriate signals to their receivers
    before code is run, and disconnecting them afterward.
    """
    handle_changed_object = curry(_handle_changed_object, request)
    handle_deleted_object = curry(_handle_deleted_object, request)

    # Connect our receivers to the post_save and post_delete signals
    post_save.connect(handle_changed_object, dispatch_uid="handle_changed_object")
    m2m_changed.connect(handle_changed_object, dispatch_uid="handle_changed_object")
    pre_delete.connect(handle_deleted_object, dispatch_uid="handle_deleted_object")

    yield

    # Disconnect change logging signals
    post_save.disconnect(handle_changed_object, dispatch_uid="handle_changed_object")
    m2m_changed.disconnect(handle_changed_object, dispatch_uid="handle_changed_object")
    pre_delete.disconnect(handle_deleted_object, dispatch_uid="handle_deleted_object")
