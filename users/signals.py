import logging

from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    logger = logging.getLogger("peering_manager.auth.login")
    username = credentials.get("username")
    logger.info(f"Failed login attempt for username: {username}")
