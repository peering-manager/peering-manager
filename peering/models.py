from __future__ import unicode_literals

from jinja2 import Template
import ipaddress
import napalm

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .fields import ASNField, CommunityField
from peeringdb.api import PeeringDB


class AutonomousSystem(models.Model):
    asn = ASNField(unique=True)
    name = models.CharField(max_length=128)
    comment = models.TextField(blank=True)
    irr_as_set = models.CharField(max_length=255, blank=True, null=True)
    ipv6_max_prefixes = models.PositiveIntegerField(blank=True, null=True)
    ipv4_max_prefixes = models.PositiveIntegerField(blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['asn']

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        super(AutonomousSystem, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('peering:as_details', kwargs={'asn': self.asn})

    def get_peering_sessions_count(self):
        return self.peeringsession_set.count()

    def get_internet_exchanges(self):
        internet_exchanges = []

        for session in self.peeringsession_set.all():
            if session.internet_exchange not in internet_exchanges:
                internet_exchanges.append(session.internet_exchange)

        return internet_exchanges

    def get_internet_exchanges_count(self):
        return len(self.get_internet_exchanges())

    def sync_with_peeringdb(self):
        peeringdb_info = PeeringDB().get_autonomous_system(self.asn)

        if not peeringdb_info:
            return False

        self.name = peeringdb_info.name
        self.ipv6_max_prefixes = peeringdb_info.info_prefixes6
        self.ipv4_max_prefixes = peeringdb_info.info_prefixes4
        self.save()

        return True

    def __str__(self):
        return 'AS{} - {}'.format(self.asn, self.name)


class Community(models.Model):
    name = models.CharField(max_length=128)
    value = CommunityField(max_length=50)
    comment = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'communities'
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('peering:community_details', kwargs={'id': self.id})

    def __str__(self):
        return self.name


class ConfigurationTemplate(models.Model):
    name = models.CharField(max_length=128)
    template = models.TextField()
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        super(ConfigurationTemplate, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('peering:configuration_template_details', kwargs={'id': self.id})

    def __str__(self):
        return self.name


class InternetExchange(models.Model):
    peeringdb_id = models.PositiveIntegerField(blank=True, null=True)
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    ipv6_address = models.GenericIPAddressField(blank=True, null=True)
    ipv4_address = models.GenericIPAddressField(blank=True, null=True)
    comment = models.TextField(blank=True)
    configuration_template = models.ForeignKey(
        'ConfigurationTemplate', blank=True, null=True, on_delete=models.SET_NULL)
    router = models.ForeignKey(
        'Router', blank=True, null=True, on_delete=models.SET_NULL)
    communities = models.ManyToManyField('Community', blank=True)

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('peering:ix_details', kwargs={'slug': self.slug})

    def get_peer_list_url(self):
        return reverse('peering:ix_peers', kwargs={'slug': self.slug})

    def get_peering_sessions_count(self):
        return self.peeringsession_set.count()

    def get_autonomous_systems(self):
        autonomous_systems = []

        for session in self.peeringsession_set.all():
            if session.autonomous_system not in autonomous_systems:
                autonomous_systems.append(session.autonomous_system)

        return autonomous_systems

    def get_autonomous_systems_count(self):
        return len(self.get_autonomous_systems())

    def get_prefixes(self):
        return [] if not self.peeringdb_id else PeeringDB().get_prefixes_for_ix_network(self.peeringdb_id)

    def get_config(self):
        peering_sessions = self.peeringsession_set.all()

        peering_sessions6 = []
        peering_sessions4 = []

        # Sort peering sessions based on IP protocol version
        for session in peering_sessions:
            session_dict = session.to_dict()

            if session_dict['ip_version'] == 6:
                peering_sessions6.append(session_dict)
            if session_dict['ip_version'] == 4:
                peering_sessions4.append(session_dict)

        peering_groups = [
            {'name': 'ipv6', 'sessions': peering_sessions6},
            {'name': 'ipv4', 'sessions': peering_sessions4},
        ]

        # Generate list of communities
        communities = []
        for community in self.communities.all():
            communities.append({
                'name': community.name,
                'value': community.value,
            })

        values = {
            'internet_exchange': self,
            'peering_groups': peering_groups,
            'communities': communities,
        }

        # Load and render the template using Jinja2
        configuration_template = Template(
            self.configuration_template.template)

        return configuration_template.render(values)

    def get_available_peers(self):
        peers = []

        # Not linked to PeeringDB, cannot determine peers
        if not self.peeringdb_id:
            return peers

        # Get the LAN that we are attached to and retrieve the peers
        api = PeeringDB()
        lan = api.get_ix_network(self.peeringdb_id)
        peeringdb_peers = api.get_peers_for_ix(lan.ix_id)
        known_peerings = []

        # Grab all addresses we are connected to
        for session in self.peeringsession_set.all():
            known_peerings.append(ipaddress.ip_address(session.ip_address))

        # Check if peers addresses are in the list of addresses we are already
        # connected to.
        for peeringdb_peer in peeringdb_peers:
            peeringdb_peer['has_ipv6'] = True if peeringdb_peer['network_ixlan'].ipaddr6 else None
            peeringdb_peer['has_ipv4'] = True if peeringdb_peer['network_ixlan'].ipaddr4 else None
            peeringdb_peer['peering6'] = peeringdb_peer['has_ipv6'] and ipaddress.ip_address(
                peeringdb_peer['network_ixlan'].ipaddr6) in known_peerings
            peeringdb_peer['peering4'] = peeringdb_peer['has_ipv4'] and ipaddress.ip_address(
                peeringdb_peer['network_ixlan'].ipaddr4) in known_peerings
            peeringdb_peer['internet_exchange'] = self

            peers.append(peeringdb_peer)

        return peers

    def __str__(self):
        return self.name


class PeeringSession(models.Model):
    autonomous_system = models.ForeignKey(
        'AutonomousSystem', on_delete=models.CASCADE)
    internet_exchange = models.ForeignKey(
        'InternetExchange', on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    comment = models.TextField(blank=True)

    def to_dict(self):
        ip_version = ipaddress.ip_address(str(self.ip_address)).version

        # Enforce max prefixes to be set to 0 by default
        max_prefixes = 0

        # Set max prefixes based on IP version
        if ip_version == 6 and self.autonomous_system.ipv6_max_prefixes:
            max_prefixes = self.autonomous_system.ipv6_max_prefixes
        if ip_version == 4 and self.autonomous_system.ipv4_max_prefixes:
            max_prefixes = self.autonomous_system.ipv4_max_prefixes

        return {
            'peer_as': self.autonomous_system.asn,
            'peer_as_name': self.autonomous_system.name,
            'ip_version': ip_version,
            'ip_address': self.ip_address,
            'max_prefixes': max_prefixes,
        }

    def get_absolute_url(self):
        return reverse('peering:peering_session_details', kwargs={'id': self.id})

    def __str__(self):
        return '{} - AS{} - IP {}'.format(self.internet_exchange.name, self.autonomous_system.asn, self.ip_address)


class Router(models.Model):
    # Platform constants, based on NAPALM drivers
    PLATFORM_JUNOS = 'junos'
    PLATFORM_IOSXR = 'iosxr'
    PLATFORM_NONE = None
    PLATFORM_CHOICES = (
        (PLATFORM_JUNOS, 'Juniper JUNOS'),
        (PLATFORM_IOSXR, 'Cisco IOS-XR'),
        (PLATFORM_NONE, 'Other'),
    )

    name = models.CharField(max_length=128)
    hostname = models.CharField(max_length=256)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, blank=True,
                                help_text='The router platform, used to interact with it')
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('peering:router_details', kwargs={'id': self.id})

    def get_napalm_device(self):
        try:
            # Driver found, instanciate it
            driver = napalm.get_network_driver(self.platform)
            return driver(hostname=self.hostname,
                          username=settings.NAPALM_USERNAME,
                          password=settings.NAPALM_PASSWORD,
                          timeout=settings.NAPALM_TIMEOUT,
                          optional_args=settings.NAPALM_ARGS)
        except napalm.base.exceptions.ModuleImportError:
            # Unable to import proper driver from napalm
            # Most probably due to a broken install
            return None

    def test_napalm_connection(self):
        device = self.get_napalm_device()
        success = False

        if device:
            try:
                # Open and close the connection just for test
                device.open()
                device.close()

                success = True
            except Exception:
                pass

        return success

    def set_configuration(self, config, commit=False):
        try:
            # Connect to the device
            device = self.get_napalm_device()
            device.open()

            # Load the config and get the diff
            device.load_merge_candidate(config=config)
            changes = device.compare_config()

            # Commit the config if needed
            if commit:
                device.commit_config()
            else:
                device.discard_config()

            device.close()
        except Exception:
            changes = None

        # Return the config diff
        return changes

    def __str__(self):
        return self.name
