import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserPreferences


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    logger = logging.getLogger("peering.manager.auth.login")
    username = credentials.get("username")
    logger.info(f"Failed login attempt for username: {username}")


@receiver(post_save, sender=User)
def create_userpreferences(instance, created, **kwargs):
    """
    Creates a new `UserPreferences` when a new `User` is created.
    """
    if created:
        UserPreferences(user=instance, data=settings.DEFAULT_USER_PREFERENCES).save()
