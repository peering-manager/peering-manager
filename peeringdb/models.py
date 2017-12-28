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


class Synchronization(models.Model):
    time = models.DateTimeField()
    number_of_objects = models.PositiveIntegerField()

    class Meta:
        ordering = ['-time']

    def __str__(self):
        return 'Synced {} objects at {}'.format(self.number_of_objects, self.time)
