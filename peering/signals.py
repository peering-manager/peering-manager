from cacheops import CacheMiss, cache
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import (
    DirectPeeringSession,
    InternetExchangePeeringSession,
    Router,
    Template,
)


@receiver(pre_save, sender=DirectPeeringSession)
def alter_direct_peering_session(instance, **kwargs):
    if instance.router and instance.router.encrypt_passwords:
        instance.encrypt_password(instance.router.platform, commit=False)


@receiver(pre_save, sender=InternetExchangePeeringSession)
def alter_internet_exchange_peering_session(instance, **kwargs):
    # Remove the IP address of this session from potential sessions for the AS
    # if it is in the list
    if (
        instance.ip_address
        in instance.autonomous_system.potential_internet_exchange_peering_sessions
    ):
        instance.autonomous_system.potential_internet_exchange_peering_sessions.remove(
            instance.ip_address
        )
        instance.autonomous_system.save()

    # Change encrypted password
    if (
        instance.internet_exchange.router
        and instance.internet_exchange.router.encrypt_passwords
    ):
        instance.encrypt_password(
            instance.internet_exchange.router.platform, commit=False
        )


@receiver(post_save, sender=Router)
def invalidate_router_cached_configuration(instance, **kwargs):
    cached_config_name = f"configuration_router_{instance.pk}"
    try:
        # Unset configuration cache if router instance is changed
        cache.get(cached_config_name)
        cache.delete(cached_config_name)
    except CacheMiss:
        pass


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
            pass
