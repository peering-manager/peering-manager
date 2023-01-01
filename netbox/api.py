import logging

import pynetbox
from django.conf import settings


class NetBox(object):
    """
    Class used to interact with the NetBox API.
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

    def napalm(self, device_id, method):
        """
        Runs the given NAPALM method on the device via the NetBox API.
        """
        self.logger.debug(f"calling dcim.devices.get: {device_id}")
        device = self.api.dcim.devices.get(device_id)
        self.logger.debug(f"calling napalm: {method}")
        result = device.napalm.list(method=method)
        return next(result)[method]
