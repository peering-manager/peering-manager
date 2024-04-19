from django.db.models.signals import pre_save
from django.dispatch import Signal, receiver

from .models import DirectPeeringSession, InternetExchangePeeringSession, Router

__all__ = (
    "post_configuration_rendering",
    "pre_configuration_rendering",
    "post_device_configuration",
    "pre_device_configuration",
)

post_configuration_rendering = Signal()
pre_configuration_rendering = Signal()
post_device_configuration = Signal()
pre_device_configuration = Signal()


@receiver(pre_save, sender=DirectPeeringSession)
def alter_direct_peering_session(instance, **kwargs):
    instance.encrypt_password(commit=False)


@receiver(pre_save, sender=InternetExchangePeeringSession)
def alter_internet_exchange_peering_session(instance, **kwargs):
    instance.encrypt_password(commit=False)


@receiver(pre_save, sender=Router)
def alter_router(instance, **kwargs):
    if not instance.poll_bgp_sessions_state and instance.poll_bgp_sessions_last_updated:
        instance.poll_bgp_sessions_last_updated = None
