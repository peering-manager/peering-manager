from __future__ import unicode_literals

from django.db import models
from .fields import ASNField


class AutonomousSystem(models.Model):
    asn = ASNField()
    name = models.CharField(max_length=128)
    comment = models.TextField(blank=True)
    ipv6_as_set = models.CharField(max_length=128)
    ipv4_as_set = models.CharField(max_length=128)
    ipv6_max_prefixes = models.PositiveIntegerField()
    ipv4_max_prefixes = models.PositiveIntegerField()

    class Meta:
        ordering = ['asn']

    def get_peering_sessions_count(self):
        return self.peeringsession_set.count()

    def get_internet_exchanges(self):
        internet_exchanges = []

        for session in self.peeringsession_set.all():
            if not session.internet_exchange in internet_exchanges:
                internet_exchanges.append(session.internet_exchange)

        return internet_exchanges

    def get_internet_exchanges_count(self):
        return len(self.get_internet_exchanges())

    def __str__(self):
        return 'AS{} - {}'.format(self.asn, self.name)


class InternetExchange(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField()
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def get_peering_sessions_count(self):
        return self.peeringsession_set.count()

    def get_autonomous_systems(self):
        autonomous_systems = []

        for session in self.peeringsession_set.all():
            if not session.autonomous_system in autonomous_systems:
                autonomous_systems.append(session.autonomous_system)

        return autonomous_systems

    def get_autonomous_systems_count(self):
        return len(self.get_autonomous_systems())

    def __str__(self):
        return self.name


class PeeringSession(models.Model):
    autonomous_system = models.ForeignKey(
        'AutonomousSystem', on_delete=models.CASCADE)
    internet_exchange = models.ForeignKey(
        'InternetExchange', on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    comment = models.TextField(blank=True)

    def __str__(self):
        return '{} - AS{} - IP {}'.format(self.internet_exchange.name, self.autonomous_system.asn, self.ip_address)
