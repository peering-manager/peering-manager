import logging

from django.conf import settings
from django.contrib.auth.models import Group
from social_core.storage import NO_ASCII_REGEX, NO_SPECIAL_REGEX


def clean_username(value):
    """
    Clean username by removing unsupported characters.
    """
    return NO_SPECIAL_REGEX.sub("", NO_ASCII_REGEX.sub("", value)).replace(":", "")


def user_default_groups_handler(backend, user, response, *args, **kwargs):
    """
    Custom pipeline handler which adds remote auth users to the default group
    specified in theconfiguration file.
    """
    logger = logging.getLogger(
        "peering_manager.authentication.user_default_groups_handler"
    )
    if settings.REMOTE_AUTH_DEFAULT_GROUPS:
        # Assign default groups to the user
        group_list = []
        for name in settings.REMOTE_AUTH_DEFAULT_GROUPS:
            try:
                group_list.append(Group.objects.get(name=name))
            except Group.DoesNotExist:
                logging.error(
                    f"could not assign group {name} to remote user {user}: group not found"
                )
        if group_list:
            user.groups.add(*group_list)
        else:
            logger.info(
                f"no valid group assignments for {user} - REMOTE_AUTH_DEFAULT_GROUPS may be incorrectly set?"
            )
