import json
import logging
import requests

from django.conf import settings


NAMESPACES = {"dcim": "dcim"}


class NetBox(object):
    """
    Class used to interact with the NetBox API.
    """

    logger = logging.getLogger("peering.manager.netbox")

    def lookup(self, namespace, search):
        """
        Sends a get request to the API given a namespace and some parameters.
        """
        # Enforce trailing slash and add namespace
        api_url = settings.NETBOX_API.strip("/") + "/" + namespace

        # Set token in the headers
        headers = {
            "accept": "application/json",
            "authorization": "Token {}".format(settings.NETBOX_API_TOKEN),
        }

        # Make the request
        self.logger.debug("calling api: %s | %s", api_url, search)
        response = requests.get(api_url, headers=headers, params=search)

        return response.json() if response.status_code == 200 else None

    def get_devices(self):
        """
        Return all devices found with the NetBox API.
        """
        result = self.lookup(NAMESPACES["dcim"] + "/devices", {})

        if not result or result["count"] == 0:
            return None

        return [
            device
            for device in result["results"]
            if device["device_role"]["slug"] in settings.NETBOX_DEVICE_ROLES
        ]

    def napalm(self, device_id, method):
        """
        Runs method on device via the NetBox API.
        """
        path = "{}/devices/{}/napalm/".format(NAMESPACES["dcim"], device_id)
        return self.lookup(path, {"method": method})[method]
