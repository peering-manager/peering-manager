from __future__ import unicode_literals

from django.db import models

from peering.fields import ASNField


class Network(models.Model):
    asn = ASNField(unique=True)
    name = models.CharField(max_length=255)
    irr_as_set = models.CharField(max_length=255, blank=True, null=True)
    info_prefixes6 = models.PositiveIntegerField(blank=True, null=True)
    info_prefixes4 = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['asn']

    def __str__(self):
        return 'AS{} - {}'.format(self.asn, self.name)


class NetworkIXLAN(models.Model):
    asn = ASNField()
    name = models.CharField(max_length=255)
    ipaddr6 = models.GenericIPAddressField(
        protocol='IPv6', blank=True, null=True)
    ipaddr4 = models.GenericIPAddressField(
        protocol='IPv4', blank=True, null=True)
    is_rs_peer = models.BooleanField(default=False)
    ix_id = models.PositiveIntegerField()

    class Meta:
        ordering = ['asn', 'ipaddr6', 'ipaddr4']

    def __str__(self):
        return 'AS{} at {} - IPv6: {} - IPv4: {}'.format(self.asn, self.name, self.ipaddr6, self.ipaddr4)


class Synchronization(models.Model):
    time = models.DateTimeField()
    number_of_objects = models.PositiveIntegerField()

    class Meta:
        ordering = ['-time']

    def __str__(self):
        return 'Synced {} objects at {}'.format(self.number_of_objects, self.time)
