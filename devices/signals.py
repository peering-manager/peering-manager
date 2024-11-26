from django.db.models.signals import pre_save
from django.dispatch import Signal, receiver

from .models import Router

__all__ = (
    "post_configuration_rendering",
    "post_device_configuration",
    "pre_configuration_rendering",
    "pre_device_configuration",
)

post_configuration_rendering = Signal()
pre_configuration_rendering = Signal()
post_device_configuration = Signal()
pre_device_configuration = Signal()


@receiver(pre_save, sender=Router)
def alter_router(instance, **kwargs):
    if not instance.poll_bgp_sessions_state and instance.poll_bgp_sessions_last_updated:
        instance.poll_bgp_sessions_last_updated = None
