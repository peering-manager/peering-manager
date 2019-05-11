import logging
import pynetbox

from django.conf import settings


NAMESPACES = {"dcim": "dcim"}


class NetBox(object):
    """
    Class used to interact with the NetBox API.
    """

    logger = logging.getLogger("peering.manager.netbox")

    api = None
    if settings.NETBOX_API:
        # pynetbox adds /api on its own. strip it off here to maintain
        # backward compatibility with earlier Peering Manager behavior
        base_url = settings.NETBOX_API.strip("/")
        if base_url.endswith("/api"):
            base_url = base_url[:-3]
        api = pynetbox.api(base_url, token=settings.NETBOX_API_TOKEN)

    def get_devices(self):
        """
        Return all devices found with the NetBox API.
        """
        self.logger.debug(
            "calling dcim.devices.filter: role=%s", settings.NETBOX_DEVICE_ROLES
        )
        result = self.api.dcim.devices.filter(role=settings.NETBOX_DEVICE_ROLES)

        if not result:
            return None

        return result

    def napalm(self, device_id, method):
        """
        Runs the given NAPALM method on the device via the NetBox API.
        """
        self.logger.debug("calling dcim.devices.get: %d", device_id)
        device = self.api.dcim.devices.get(device_id)
        self.logger.debug("calling napalm: %s", method)
        result = device.napalm.list(method=method)
        return result[method]
