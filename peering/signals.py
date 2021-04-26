import logging

from cacheops import CacheMiss, cache
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import (
    DirectPeeringSession,
    InternetExchangePeeringSession,
    Router,
    Template,
)

logger = logging.getLogger("peering.manager.peering.signals")


@receiver(pre_save, sender=DirectPeeringSession)
def alter_direct_peering_session(instance, **kwargs):
    instance.encrypt_password(commit=False)


@receiver(pre_save, sender=InternetExchangePeeringSession)
def alter_internet_exchange_peering_session(instance, **kwargs):
    instance.encrypt_password(commit=False)


@receiver(post_save, sender=Router)
def invalidate_router_cached_configuration(instance, **kwargs):
    cached_config_name = f"configuration_router_{instance.pk}"
    try:
        # Unset configuration cache if router instance is changed
        cache.get(cached_config_name)
        cache.delete(cached_config_name)
    except CacheMiss:
        logger.debug(f"unable to find cached config '{cached_config_name}'")


@receiver(post_save, sender=Template)
def invalidate_cached_configuration_by_template(instance, **kwargs):
    # Unset configuration for each router using the changed template
    for router in Router.objects.filter(configuration_template=instance):
        cached_config_name = f"configuration_router_{router.pk}"
        try:
            # Unset configuration cache if router instance is changed
            cache.get(cached_config_name)
            cache.delete(cached_config_name)
        except CacheMiss:
            logger.debug(f"unable to find cached config '{cached_config_name}'")
