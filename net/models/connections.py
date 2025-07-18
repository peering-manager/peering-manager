import logging

from django.db import models
from netfields import InetAddressField, MACAddressField, NetManager

from peering_manager.models import PrimaryModel
from peeringdb.models import NetworkIXLan
from utils.validators import AddressFamilyValidator, MACAddressValidator

from ..enums import ConnectionStatus
from ..fields import VLANField

logger = logging.getLogger("peering.manager.net")

__all__ = ("Connection",)


class Connection(PrimaryModel):
    peeringdb_netixlan = models.ForeignKey(
        to="peeringdb.NetworkIXLan", on_delete=models.SET_NULL, blank=True, null=True
    )
    status = models.CharField(
        max_length=20, choices=ConnectionStatus, default=ConnectionStatus.ENABLED
    )
    vlan = VLANField(verbose_name="VLAN", blank=True, null=True)
    mac_address = MACAddressField(
        verbose_name="MAC address",
        blank=True,
        null=True,
        validators=[MACAddressValidator],
    )
    ipv6_address = InetAddressField(
        store_prefix_length=True,
        blank=True,
        null=True,
        validators=[AddressFamilyValidator(6)],
    )
    ipv4_address = InetAddressField(
        store_prefix_length=True,
        blank=True,
        null=True,
        validators=[AddressFamilyValidator(4)],
    )
    internet_exchange_point = models.ForeignKey(
        to="peering.InternetExchange", blank=True, null=True, on_delete=models.CASCADE
    )
    router = models.ForeignKey(
        to="devices.Router", blank=True, null=True, on_delete=models.SET_NULL
    )
    interface = models.CharField(max_length=200, blank=True)

    objects = NetManager()

    class Meta:
        ordering = ["internet_exchange_point", "router"]

    @property
    def name(self) -> str:
        return str(self)

    @property
    def linked_to_peeringdb(self) -> bool:
        """
        Tells if the PeeringDB object for this connection still exists.
        """
        return self.peeringdb_netixlan is not None

    def __str__(self) -> str:
        s = ""

        if self.internet_exchange_point:
            s += str(self.internet_exchange_point)

        if self.router:
            if s:
                s += " on "
            s += str(self.router)

            if self.interface:
                s += f" {self.interface}"

        return s or f"Connection #{self.pk}"

    def get_status_colour(self) -> str:
        return ConnectionStatus.colours.get(self.status)

    def link_to_peeringdb(self) -> NetworkIXLan | None:
        """
        Retrieves the PeeringDB ID for this IX connection based on the IP addresses
        that have been recorded. The PeeringDB record will be returned on success. In
        any other cases `None` will be returned. The value will also be saved in the
        corresponding field of the model.
        """

        # If data imported from PeeringDB doesn't have IPs set, ignore it
        if self.ipv4_address is None and self.ipv6_address is None:
            return None

        # Prepare value for database lookup
        ipaddr6 = (
            self.ipv6_address.ip
            if hasattr(self.ipv6_address, "ip")
            else self.ipv6_address
        )
        ipaddr4 = (
            self.ipv4_address.ip
            if hasattr(self.ipv4_address, "ip")
            else self.ipv4_address
        )

        try:
            netixlan = NetworkIXLan.objects.get(ipaddr6=ipaddr6, ipaddr4=ipaddr4)
            logger.debug(f"linked connection {self} (pk: {self.pk}) to peeringdb")
        except NetworkIXLan.DoesNotExist:
            logger.debug(
                f"linking connection {self} (pk: {self.pk}) to peeringdb failed"
            )
            return None

        self.peeringdb_netixlan = netixlan
        self.save()

        return netixlan

    def ixapi_network_service_config(self):
        """
        Returns the corresponding IX-API network service config for this connection.
        """
        if (
            not self.internet_exchange_point
            or not self.internet_exchange_point.ixapi_endpoint
        ):
            return None

        for (
            config
        ) in self.internet_exchange_point.ixapi_endpoint.get_network_service_configs():
            if config.connection == self:
                return config

        return None

    def ixapi_mac_address(self, network_service_config):
        """
        Returns the MAC address found in IX-API for this connection.
        """
        if not network_service_config or not len(network_service_config.macs):
            return None

        return network_service_config.macs[0]

    def set_ixapi_mac_address(self):
        """
        Calls IX-API to set the MAC address to be used by the network service config
        related to this connection.
        """
        if not self.mac_address:
            # If connection has not MAC, update cannot be performed
            logger.debug(
                f"connection #{self.pk} has no mac address, cannot change in ix-api"
            )
            return False

        network_service_config = self.ixapi_network_service_config()
        if not network_service_config:
            # If connection has not IX-API network service config, update cannot be
            # performed
            logger.debug(
                f"cannot find ix-api network service config for connection #{self.pk}"
            )
            return False

        mac = self.internet_exchange_point.ixapi_endpoint.create_mac_address(
            self.mac_address
        )
        if not mac:
            # If MAC failed to be created and does not already exist, update cannot be
            # performed
            logger.debug(
                f"cannot create mac address {self.mac_address} in ix-api for connection #{self.pk}"
            )
            return False

        logger.debug(
            f"changing ix-api connection mac to {mac} on nsc {network_service_config} for connection #{self.pk}"
        )
        return network_service_config.update({"macs": [mac]})
