from __future__ import unicode_literals

import ipaddress
import logging
import napalm

from jinja2 import Template

from django.conf import settings
from django.db import models, transaction
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

    @staticmethod
    def does_exist(asn):
        try:
            return AutonomousSystem.objects.get(asn=asn)
        except AutonomousSystem.DoesNotExist:
            return None

    @staticmethod
    def create_from_peeringdb(asn):
        peeringdb_network = PeeringDB().get_autonomous_system(asn)

        if not peeringdb_network:
            return None

        try:
            return AutonomousSystem.objects.get(asn=peeringdb_network.asn)
        except AutonomousSystem.DoesNotExist:
            values = {
                'asn': peeringdb_network.asn,
                'name': peeringdb_network.name,
                'irr_as_set': peeringdb_network.irr_as_set,
                'ipv6_max_prefixes': peeringdb_network.info_prefixes6,
                'ipv4_max_prefixes': peeringdb_network.info_prefixes4,
            }
            autonomous_system = AutonomousSystem(**values)
            autonomous_system.save()

        return autonomous_system

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
        return reverse('peering:community_details', kwargs={'pk': self.pk})

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
        return reverse('peering:configuration_template_details', kwargs={'pk': self.pk})

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

    logger = logging.getLogger('peering.manager.peering')

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('peering:ix_details', kwargs={'slug': self.slug})

    def get_peering_sessions_list_url(self):
        return reverse('peering:ix_peering_sessions', kwargs={'slug': self.slug})

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

    def import_peering_sessions_from_router(self):
        # No point of discovering from router if platform is none or is not
        # supported or if the IX is not linked to a PeeringDB record.
        if not self.router or not self.router.platform or not self.peeringdb_id:
            return None

        number_of_peering_sessions = 0
        number_of_autonomous_systems = 0
        # Build a list based on prefixes based on PeeringDB records
        prefixes = [ipaddress.ip_network(prefix['prefix'])
                    for prefix in self.get_prefixes()]
        # No prefixes found
        if not prefixes:
            self.logger.debug('no prefixes found for %s', self.name.lower())
            return None
        else:
            self.logger.debug('found %s prefixes (%s) for %s', len(prefixes), ', '.join(
                [str(prefix) for prefix in prefixes]), self.name.lower())

        # Gather all existing BGP sessions from the router connected to the IX
        bgp_sessions = self.router.get_napalm_bgp_neighbors()

        with transaction.atomic():
            # For each BGP session check if the address fits in on of the prefixes
            for bgp_session in bgp_sessions:
                for prefix in prefixes:
                    self.logger.debug(
                        'checking for sessions inside prefix %s', str(prefix))

                    # If the address fits, create a new PeeringSession object and a
                    # new AutonomousSystem object if they does not exist already
                    if bgp_session['ip_address'] in prefix:
                        self.logger.debug('session %s fitting inside prefix %s', str(
                            bgp_session['ip_address']), str(prefix))

                        if not PeeringSession.does_exist(str(bgp_session['ip_address'])):
                            autonomous_system = AutonomousSystem.does_exist(
                                bgp_session['remote_asn'])
                            if not autonomous_system:
                                autonomous_system = AutonomousSystem.create_from_peeringdb(
                                    bgp_session['remote_asn'])
                                # Do not count the AS if it does not have a
                                # PeeringDB record
                                if autonomous_system:
                                    number_of_autonomous_systems += 1

                            # Only add a peering session if we were able to
                            # find the AS on PeeringDB
                            if autonomous_system:
                                values = {
                                    'autonomous_system': autonomous_system,
                                    'internet_exchange': self,
                                    'ip_address': str(bgp_session['ip_address']),
                                }
                                peering_session = PeeringSession(**values)
                                peering_session.save()
                                number_of_peering_sessions += 1
                    else:
                        self.logger.debug('session %s not fitting inside prefix %s', str(
                            bgp_session['ip_address']), str(prefix))

        return (number_of_autonomous_systems, number_of_peering_sessions)

    def __str__(self):
        return self.name


class PeeringSession(models.Model):
    autonomous_system = models.ForeignKey(
        'AutonomousSystem', on_delete=models.CASCADE)
    internet_exchange = models.ForeignKey(
        'InternetExchange', on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    comment = models.TextField(blank=True)

    @staticmethod
    def does_exist(ip_address):
        try:
            PeeringSession.objects.get(ip_address=ip_address)
        except PeeringSession.DoesNotExist:
            return False
        return True

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
        return reverse('peering:peering_session_details', kwargs={'pk': self.pk})

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

    logger = logging.getLogger('peering.manager.napalm')

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('peering:router_details', kwargs={'pk': self.pk})

    def get_napalm_device(self):
        self.logger.debug('looking for napalm driver "%s"', self.platform)
        try:
            # Driver found, instanciate it
            driver = napalm.get_network_driver(self.platform)
            self.logger.debug('found napalm driver "%s"', self.platform)
            return driver(hostname=self.hostname,
                          username=settings.NAPALM_USERNAME,
                          password=settings.NAPALM_PASSWORD,
                          timeout=settings.NAPALM_TIMEOUT,
                          optional_args=settings.NAPALM_ARGS)
        except napalm.base.exceptions.ModuleImportError:
            # Unable to import proper driver from napalm
            # Most probably due to a broken install
            self.logger.error(
                'no napalm driver "%s" found (not installed or does not exist)', self.platform)
            return None

    def open_napalm_device(self, device):
        """
        Opens a connection with a device using NAPALM.

        This method returns True if the connection is properly opened or False
        in any other cases. It handles exceptions that can occur during the
        connection opening process by itself.

        It is a wrapper method mostly used for logging purpose.
        """
        success = False

        if not device:
            return success

        try:
            self.logger.debug('connecting to %s', self.hostname)
            device.open()
        except napalm.base.exceptions.ConnectionException as e:
            self.logger.error(
                'error while trying to connect to %s reason "%s"', self.hostname, e)
        except Exception:
            self.logger.error(
                'error while trying to connect to %s', self.hostname)
        else:
            self.logger.debug('successfully connected to %s', self.hostname)
            success = True
        finally:
            return success

    def close_napalm_device(self, device):
        """
        Closes a connection with a device using NAPALM.

        This method returns True if the connection is properly closed or False
        if the device is not valid.

        It is a wrapper method mostly used for logging purpose.
        """
        if not device:
            return False

        device.close()
        self.logger.debug('closing connection with %s', self.hostname)

        return True

    def test_napalm_connection(self):
        """
        Opens and closes a connection with a device using NAPALM to see if it
        is possible to interact with it.

        This method returns True only if the connection opening and closing are
        both successful.
        """
        device = self.get_napalm_device()

        # Open and close the test_napalm_connection
        self.logger.debug('testing connection with %s', self.hostname)
        opened = self.open_napalm_device(device)
        closed = self.close_napalm_device(device)

        # Issue while opening or closing the connection
        if not opened or not closed:
            self.logger.error(
                'cannot connect to % s, napalm functions won\'t work', self.hostname)

        return (opened and closed)

    def set_napalm_configuration(self, config, commit=False):
        """
        Tries to merge a given configuration on a device using NAPALM.

        This methods returns the changes applied to the configuration if the
        merge was successful. It will return None in any other cases.

        The optional named argument 'commit' is a boolean which is used to
        know if the changes must be commited or discarded. The default value is
        False which means that the changes will be discarded.
        """
        changes = None

        device = self.get_napalm_device()
        opened = self.open_napalm_device(device)

        if opened:
            try:
                # Load the config
                self.logger.debug('merging configuration on %s', self.hostname)
                device.load_merge_candidate(config=config)

                # Get the config diff
                self.logger.debug(
                    'checking for configuration changes on %s', self.hostname)
                changes = device.compare_config()
                self.logger.debug('raw napalm output %s', changes)

                # Commit the config if required
                if commit:
                    self.logger.debug(
                        'commiting configuration on %s', self.hostname)
                    device.commit_config()

                else:
                    self.logger.debug(
                        'discarding configuration on %s', self.hostname)
                    device.discard_config()
            except napalm.base.exceptions.MergeConfigException as e:
                self.logger.debug(
                    'unable to merge configuration on %s reason "%s"', self.hostname, e)
            except Exception:
                self.logger.debug(
                    'unable to merge configuration on %s', self.hostname)
            else:
                self.logger.debug(
                    'successfully merged configuration on %s', self.hostname)
            finally:
                closed = self.close_napalm_device(device)
                if not closed:
                    self.logger.debug(
                        'error while closing connection with %s', self.hostname)

        return changes

    def _napalm_bgp_neighbors_to_peer_list(self, napalm_dict):
        bgp_peers = []

        if not napalm_dict:
            return bgp_peers

        # For each VRF
        for vrf in napalm_dict:
            # Get peers inside it
            peers = napalm_dict[vrf]['peers']
            self.logger.debug('found %s bgp neighbors in %s vrf on %s', len(
                peers), vrf, self.hostname)

            # For each peer handle its IP address and the needed details
            for ip, details in peers.items():
                if 'remote_as' not in details:
                    # See NAPALM issue #659
                    # https://github.com/napalm-automation/napalm/issues/659
                    self.logger.debug(
                        'ignored bgp neighbor %s in %s vrf on %s', ip, vrf, self.hostname)
                elif ip in [str(i['ip_address']) for i in bgp_peers]:
                    self.logger.debug(
                        'duplicate bgp neighbor %s on %s', ip, self.hostname)
                else:
                    try:
                        # Save the BGP session (IP and remote ASN)
                        bgp_peers.append({
                            'ip_address': ipaddress.ip_address(ip),
                            'remote_asn': details['remote_as'],
                        })
                    except ValueError as e:
                        # Error while parsing the IP address
                        self.logger.error(
                            'ignored bgp neighbor %s in %s vrf on %s reason "%s"', ip, vrf, self.hostname, e)
                        # Force next iteration
                        continue

        return bgp_peers

    def get_napalm_bgp_neighbors(self):
        """
        Returns a list of dictionaries listing all BGP neighbors found on the
        router using NAPALM.

        Each dictionary contains two keys 'ip_address' and 'remote_asn'.

        If an error occurs or no BGP neighbors can be found, the returned list
        will be empty.
        """
        bgp_sessions = []

        device = self.get_napalm_device()
        opened = self.open_napalm_device(device)

        if opened:
            # Get all BGP neighbors on the router
            self.logger.debug('getting bgp neighbors on %s', self.hostname)
            bgp_neighbors = device.get_bgp_neighbors()
            self.logger.debug('raw napalm output %s', bgp_neighbors)
            self.logger.debug('found %s vrfs with bgp neighbors on %s', len(
                bgp_neighbors), self.hostname)

            bgp_sessions = self._napalm_bgp_neighbors_to_peer_list(
                bgp_neighbors)
            self.logger.debug('found %s bgp neighbors on %s',
                              len(bgp_sessions), self.hostname)

            # Close connection to the device
            closed = self.close_napalm_device(device)
            if not closed:
                self.logger.debug(
                    'error while closing connection with %s', self.hostname)

        return bgp_sessions

    def __str__(self):
        return self.name
