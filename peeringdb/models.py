import logging

from django.db import models
from netfields import CidrAddressField, InetAddressField, NetManager

from peering.fields import ASNField
from utils.validators import AddressFamilyValidator

from .constants import *


class Contact(models.Model):
    role = models.CharField(max_length=32, choices=CONTACT_ROLE_CHOICES)
    visible = models.CharField(
        max_length=64,
        choices=CONTACT_VISIBILITY_CHOICES,
        default=CONTACT_VISIBILITY_PUBLIC,
    )
    name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    url = models.URLField(max_length=255, blank=True)
    net_id = models.PositiveIntegerField()

    class Meta:
        ordering = ["net_id", "name"]

    def __str__(self):
        return "{} - {} - {}".format(self.net_id, self.role, self.name)


class Network(models.Model):
    asn = ASNField(unique=True)
    name = models.CharField(max_length=255)
    irr_as_set = models.CharField(max_length=255, blank=True, null=True)
    info_prefixes6 = models.PositiveIntegerField(blank=True, default=0)
    info_prefixes4 = models.PositiveIntegerField(blank=True, default=0)

    class Meta:
        ordering = ["asn"]

    def __str__(self):
        return "AS{} - {}".format(self.asn, self.name)


class NetworkIXLAN(models.Model):
    asn = ASNField()
    name = models.CharField(max_length=255)
    ipaddr6 = InetAddressField(
        store_prefix_length=False,
        blank=True,
        null=True,
        validators=[AddressFamilyValidator(6)],
    )
    ipaddr4 = InetAddressField(
        store_prefix_length=False,
        blank=True,
        null=True,
        validators=[AddressFamilyValidator(4)],
    )
    is_rs_peer = models.BooleanField(default=False)
    ix_id = models.PositiveIntegerField()
    ixlan_id = models.PositiveIntegerField()

    objects = NetManager()
    logger = logging.getLogger("peering.manager.peeringdb")

    class Meta:
        ordering = ["asn", "ipaddr6", "ipaddr4"]
        verbose_name = "Network IX LAN"
        verbose_name_plural = "Network IX LANs"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Ignore if we do not have any IP addresses
        if not self.ipaddr6 and not self.ipaddr4:
            self.logger.debug(
                "network ixlan with as%s and ixlan id %s ignored"
                ", no ipv6 and no ipv4",
                self.asn,
                self.ixlan_id,
            )
            return

        # Trigger the build of a new PeerRecord or just ignore if it already exists,
        # assumes it exists
        # Note that there is not point of doing the same thing when a Network
        # or a NetworkIXLAN is deleted because it will automatically delete the
        # PeerRecord linked to it using the foreign key (with the CASCADE mode)
        network = None
        peer_record_exists = True

        try:
            # Try guessing the Network given its ASN
            network = Network.objects.get(asn=self.asn)
            # Try finding if the PeerRecord already exists
            PeerRecord.objects.get(network=network, network_ixlan=self)
        except Network.DoesNotExist:
            # The network does not exist, well not much to do
            self.logger.debug(
                "network with as%s does not exist, required for "
                "peer record creation",
                self.asn,
            )
        except PeerRecord.DoesNotExist:
            # But if the exception is raised, it does not
            peer_record_exists = False

        # If the PeerRecord does not exist, create it
        if not peer_record_exists:
            PeerRecord.objects.create(network=network, network_ixlan=self)
            self.logger.debug(
                "peer record created with as%s and ixlan id %s", self.asn, self.ixlan_id
            )
        else:
            self.logger.debug(
                "peer record with as%s and ixlan id %s exists", self.asn, self.ixlan_id
            )

    def __str__(self):
        return "AS{} on {} - IPv6: {} - IPv4: {}".format(
            self.asn, self.name, self.ipaddr6, self.ipaddr4
        )


class PeerRecord(models.Model):
    network = models.ForeignKey("Network", on_delete=models.CASCADE)
    network_ixlan = models.ForeignKey("NetworkIXLAN", on_delete=models.CASCADE)
    visible = models.BooleanField(blank=True, default=True)

    def __str__(self):
        return "AS{} ({}) on {}".format(
            self.network.asn, self.network.name, self.network_ixlan.name
        )


class Prefix(models.Model):
    protocol = models.CharField(max_length=8)
    prefix = CidrAddressField()
    ixlan_id = models.PositiveIntegerField()

    objects = NetManager()

    class Meta:
        ordering = ["prefix"]
        verbose_name = "IX Prefix"
        verbose_name_plural = "IX Prefixes"

    def __str__(self):
        return "{} - {}".format(self.protocol, self.prefix)


class Synchronization(models.Model):
    time = models.DateTimeField()
    added = models.PositiveIntegerField()
    updated = models.PositiveIntegerField()
    deleted = models.PositiveIntegerField()

    class Meta:
        ordering = ["-time"]

    def __str__(self):
        return "Synced {} objects at {}".format(
            (self.added + self.deleted + self.updated), self.time
        )
