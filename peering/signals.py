import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.defaultfilters import pluralize

from .enums import RequestedSessionStatus
from .models import (
    DirectPeeringSession,
    InternetExchangePeeringSession,
    RequestedSession,
)

logger = logging.getLogger("peering.manager.peering")


@receiver(pre_save, sender=DirectPeeringSession)
def alter_direct_peering_session(instance, **kwargs):
    instance.encrypt_password(commit=False)


@receiver(pre_save, sender=InternetExchangePeeringSession)
def alter_internet_exchange_peering_session(instance, **kwargs):
    instance.encrypt_password(commit=False)


def _check_peering_request_conflict(instance, **kwargs):
    if not instance._state.adding:
        return

    conflicts = RequestedSession.objects.filter(ip_address=instance.ip_address, status=RequestedSessionStatus.PENDING)
    if not conflicts.exists():
        return

    # Only one peering request should match, we still handle several, just in case
    pr_ids = set(conflicts.values_list("peering_request__tracking_id", flat=True))
    ids = ", ".join(str(uid) for uid in pr_ids)
    message = (
        f"Cannot create session for {instance.ip_address}: already covered by "
        f"{len(pr_ids)} pending peering request{pluralize(pr_ids)} ({ids})."
    )
    if settings.PEERING_REQUEST_BLOCKS_SESSION_CREATION:
        raise ValidationError(message)
    logger.warning(message)


pre_save.connect(_check_peering_request_conflict, sender=InternetExchangePeeringSession)
pre_save.connect(_check_peering_request_conflict, sender=DirectPeeringSession)
