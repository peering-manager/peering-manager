import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.defaultfilters import pluralize

from .enums import RequestedSessionStatus
from .functions import ip_host
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


@receiver(pre_save, sender=DirectPeeringSession)
@receiver(pre_save, sender=InternetExchangePeeringSession)
def check_peering_request_conflict(instance, **kwargs):
    if not instance._state.adding or not instance.ip_address:
        return

    # Match on host address only, `RequestedSession.ip_address` stores a prefix length
    conflicts = RequestedSession.objects.filter(
        ip_address__host=str(ip_host(instance.ip_address)), status=RequestedSessionStatus.PENDING
    )

    # Ensure proper scoping
    if isinstance(instance, InternetExchangePeeringSession) and instance.ixp_connection_id:
        conflicts = conflicts.filter(ixp_connection_id=instance.ixp_connection_id)
    elif instance.autonomous_system_id:
        conflicts = conflicts.filter(peering_request__requesting_asn=instance.autonomous_system.asn)
    else:
        return

    # A session materialising an accepted request must not be blocked by the very request it comes from
    accepted_from = getattr(instance, "_accepted_from_peering_request_id", None)
    if accepted_from is not None:
        conflicts = conflicts.exclude(peering_request_id=accepted_from)

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
