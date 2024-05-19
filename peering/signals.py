from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import DirectPeeringSession, InternetExchangePeeringSession


@receiver(pre_save, sender=DirectPeeringSession)
def alter_direct_peering_session(instance, **kwargs):
    instance.encrypt_password(commit=False)


@receiver(pre_save, sender=InternetExchangePeeringSession)
def alter_internet_exchange_peering_session(instance, **kwargs):
    instance.encrypt_password(commit=False)
