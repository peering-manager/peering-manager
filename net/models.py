import ipaddress
import logging

from django.db import models
from django.urls import reverse
from netfields import InetAddressField, NetManager

from peeringdb.models import NetworkIXLan
from utils.models import ChangeLoggedModel, TaggableModel
from utils.validators import AddressFamilyValidator

from .enums import ConnectionState
from .fields import VLANField

logger = logging.getLogger("peering.manager.net")


class Connection(ChangeLoggedModel, TaggableModel):
    peeringdb_netixlan = models.ForeignKey(
        "peeringdb.NetworkIXLan", on_delete=models.SET_NULL, blank=True, null=True
    )
    state = models.CharField(
        max_length=20, choices=ConnectionState.choices, default=ConnectionState.ENABLED
    )
    vlan = VLANField(verbose_name="VLAN", blank=True, null=True)
    ipv6_address = InetAddressField(
        store_prefix_length=False,
        blank=True,
        null=True,
        validators=[AddressFamilyValidator(6)],
    )
    ipv4_address = InetAddressField(
        store_prefix_length=False,
        blank=True,
        null=True,
        validators=[AddressFamilyValidator(4)],
    )
    internet_exchange_point = models.ForeignKey(
        "peering.InternetExchange", blank=True, null=True, on_delete=models.SET_NULL
    )
    router = models.ForeignKey(
        "peering.Router", blank=True, null=True, on_delete=models.SET_NULL
    )
    interface = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=200, blank=True)
    comments = models.TextField(blank=True)

    objects = NetManager()

    @property
    def name(self):
        return str(self)

    @property
    def linked_to_peeringdb(self):
        """
        Tells if the PeeringDB object for this connection still exists.
        """
        return self.peeringdb_netixlan is not None

    def __str__(self):
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

    def get_absolute_url(self):
        return reverse("net:connection_details", kwargs={"pk": self.pk})

    def link_to_peeringdb(self):
        """
        Retrieves the PeeringDB ID for this IX connection based on the IP addresses
        that have been recorded. The PeeringDB record will be returned on success. In
        any other cases `None` will be returned. The value will also be saved in the
        corresponding field of the model.
        """
        try:
            netixlan = NetworkIXLan.objects.get(
                ipaddr6=self.ipv6_address, ipaddr4=self.ipv4_address
            )
        except NetworkIXLan.DoesNotExist:
            return None

        self.peeringdb_netixlan = netixlan
        self.save()

        return netixlan
