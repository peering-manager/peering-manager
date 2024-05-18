import logging

import pynetbox
from django.conf import settings

__all__ = ("NetBox",)


class NetBox:
    """
    Class used to interact with the NetBox API.

    FIXME: Move to another app
    """

    logger = logging.getLogger("peering.manager.netbox")

    def __init__(self, *args, **kwargs):
        self.api = None
        if settings.NETBOX_URL:
            self.api = pynetbox.api(
                settings.NETBOX_URL,
                token=settings.NETBOX_API_TOKEN,
                threading=settings.NETBOX_API_THREADING,
            )
            # Enable/disable SSL verification on user request
            self.api.http_session.verify = settings.NETBOX_API_VERIFY_SSL

    def get_devices(self):
        """
        Return all devices found with the NetBox API.
        """
        if not settings.NETBOX_DEVICE_ROLES and not settings.NETBOX_TAGS:
            return self.api.dcim.devices.all()

        filter = {}
        if settings.NETBOX_DEVICE_ROLES:
            self.logger.debug(
                f"will call dcim.devices.filter: role={settings.NETBOX_DEVICE_ROLES}"
            )
            filter["role"] = settings.NETBOX_DEVICE_ROLES
        if settings.NETBOX_TAGS:
            self.logger.debug(
                f"will call dcim.devices.filter: tag={settings.NETBOX_TAGS}"
            )
            filter["tag"] = settings.NETBOX_TAGS
        return self.api.dcim.devices.filter(**filter)
