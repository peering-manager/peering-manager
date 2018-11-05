from __future__ import unicode_literals

import ipaddress
import logging
import napalm

from jinja2 import Template

from django.conf import settings
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from .constants import (BGP_RELATIONSHIP_CHOICES, BGP_RELATIONSHIP_CUSTOMER,
                        BGP_RELATIONSHIP_PRIVATE_PEERING,
                        BGP_RELATIONSHIP_TRANSIT_PROVIDER, BGP_STATE_CHOICES,
                        BGP_STATE_IDLE, BGP_STATE_CONNECT, BGP_STATE_ACTIVE,
                        BGP_STATE_OPENSENT, BGP_STATE_OPENCONFIRM,
                        BGP_STATE_ESTABLISHED, COMMUNITY_TYPE_CHOICES,
                        COMMUNITY_TYPE_EGRESS, COMMUNITY_TYPE_INGRESS,
                        PLATFORM_CHOICES, PLATFORM_EOS, PLATFORM_IOS,
                        PLATFORM_IOSXR, PLATFORM_JUNOS)
from .fields import ASNField, CommunityField
from peeringdb.api import PeeringDB
from peeringdb.models import NetworkIXLAN, PeerRecord
from utils.models import CreatedUpdatedModel


class AutonomousSystem(CreatedUpdatedModel):
    asn = ASNField(unique=True)
    name = models.CharField(max_length=128)
    comment = models.TextField(blank=True)
    irr_as_set = models.CharField(max_length=255, blank=True, null=True)
    irr_as_set_peeringdb_sync = models.BooleanField(default=True)
    ipv6_max_prefixes = models.PositiveIntegerField(blank=True, null=True)
    ipv6_max_prefixes_peeringdb_sync = models.BooleanField(default=True)
    ipv4_max_prefixes = models.PositiveIntegerField(blank=True, null=True)
    ipv4_max_prefixes_peeringdb_sync = models.BooleanField(default=True)

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

    def get_absolute_url(self):
        return reverse('peering:autonomous_system_details', kwargs={'asn': self.asn})

    def get_internet_exchange_peering_sessions_list_url(self):
        return reverse('peering:autonomous_system_internet_exchange_peering_sessions', kwargs={'asn': self.asn})

    def get_direct_peering_sessions_list_url(self):
        return reverse('peering:autonomous_system_direct_peering_sessions', kwargs={'asn': self.asn})

    def get_peering_sessions(self):
        return self.internetexchangepeeringsession_set.all()

    def get_internet_exchanges(self):
        internet_exchanges = []

        for session in self.internetexchangepeeringsession_set.all():
            if session.internet_exchange not in internet_exchanges:
                internet_exchanges.append(session.internet_exchange)

        return internet_exchanges

    def get_common_internet_exchanges(self):
        """
        Return all IX we have in common with the AS.
        """
        # Get common IX networks between us and this AS
        common = PeeringDB().get_common_ix_networks_for_asns(settings.MY_ASN,
                                                             self.asn)
        return InternetExchange.objects.all().filter(
            peeringdb_id__in=[us.id for us, _ in common])

    def get_missing_peering_sessions(self, internet_exchange):
        """
        Returns a tuple of IP address lists. The first element of the tuple
        is the IPv6 address list. The second element of the tuple is the IPv4
        address list. Each IP address of the lists is the address of a missing
        peering session with the current AS.
        """
        if not internet_exchange:
            return None

        # Get common IX networks between us and this AS
        common = PeeringDB().get_common_ix_networks_for_asns(settings.MY_ASN,
                                                             self.asn)

        # Divide sessions based on the IP versions
        ipv6_sessions = []
        ipv4_sessions = []

        # For each common networks take a look at it
        for us, peer in common:
            # We only care about networks matching the IX we want
            if us.id == internet_exchange.peeringdb_id:
                # Check on the IPv6 address
                if peer.ipaddr6:
                    try:
                        ip_address = ipaddress.IPv6Address(peer.ipaddr6)
                        if not InternetExchangePeeringSession.does_exist(
                                internet_exchange=internet_exchange,
                                autonomous_system=self,
                                ip_address=str(ip_address)):
                            ipv6_sessions.append(ip_address)
                    except ipaddress.AddressValueError:
                        continue

                # Check on the IPv4 address
                if peer.ipaddr4:
                    try:
                        ip_address = ipaddress.IPv4Address(peer.ipaddr4)
                        if not InternetExchangePeeringSession.does_exist(
                                internet_exchange=internet_exchange,
                                autonomous_system=self,
                                ip_address=str(ip_address)):
                            ipv4_sessions.append(ip_address)
                    except ipaddress.AddressValueError:
                        continue

        return (ipv6_sessions, ipv4_sessions)

    def sync_with_peeringdb(self):
        """
        Synchronize AS properties with those found in PeeringDB.
        """
        peeringdb_info = PeeringDB().get_autonomous_system(self.asn)

        # No record found, nothing to sync
        if not peeringdb_info:
            return False

        # Always synchronize the name
        self.name = peeringdb_info.name

        # Sync other properties if we are told to do so
        if self.irr_as_set_peeringdb_sync:
            self.irr_as_set = peeringdb_info.irr_as_set
        if self.ipv6_max_prefixes_peeringdb_sync:
            self.ipv6_max_prefixes = peeringdb_info.info_prefixes6
        if self.ipv4_max_prefixes_peeringdb_sync:
            self.ipv4_max_prefixes = peeringdb_info.info_prefixes4

        # Save the new AS
        self.save()

        return True

    def __str__(self):
        return 'AS{} - {}'.format(self.asn, self.name)


class BGPSession(CreatedUpdatedModel):
    """
    Abstract class used to define common caracteristics of BGP sessions.

    A BGP session is always defined with the following fields:
      * an AS, or autonomous system, it can also be called a peer
      * an IP address used to establish the session
      * a enabled or disabled status telling if the session should be
        administratively up or not
      * a BGP state giving the current operational state of session (it will
        remain to unkown if the is disabled)
      * a received prefix count (it will stay none if polling is disabled)
      * a advertised prefix count (it will stay none if polling is disabled)
      * comments that consist of plain text that can use the markdown format
    """
    autonomous_system = models.ForeignKey(
        'AutonomousSystem', on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    password = models.CharField(max_length=255, blank=True, null=True)
    enabled = models.BooleanField(default=True)
    bgp_state = models.CharField(max_length=50, choices=BGP_STATE_CHOICES,
                                 blank=True, null=True)
    received_prefix_count = models.PositiveIntegerField(blank=True, null=True)
    advertised_prefix_count = models.PositiveIntegerField(blank=True,
                                                          null=True)
    last_state_established = models.DateField(blank=True, null=True)
    comment = models.TextField(blank=True)

    class Meta:
        abstract = True

    def get_enabled_html(self):
        """
        Return an HTML element based on the status (enabled or disabled).
        """
        badge = 'success'
        text = 'Enabled'

        if not self.enabled:
            badge = 'danger'
            text = 'Disabled'

        return mark_safe('<span class="badge badge-{}">{}</span>'.format(badge,
                                                                         text))

    def get_bgp_state_html(self):
        """
        Return an HTML element based on the BGP state.
        """
        if self.bgp_state == BGP_STATE_IDLE:
            badge = 'danger'
        elif self.bgp_state in [BGP_STATE_CONNECT, BGP_STATE_ACTIVE]:
            badge = 'warning'
        elif self.bgp_state in [BGP_STATE_OPENSENT, BGP_STATE_OPENCONFIRM]:
            badge = 'info'
        elif self.bgp_state == BGP_STATE_ESTABLISHED:
            badge = 'success'
        else:
            badge = 'secondary'

        text = '<span class="badge badge-{}">{}</span>'.format(
            badge, self.get_bgp_state_display() or 'Unknown')

        # Only if the session is established, display some details
        if self.bgp_state == BGP_STATE_ESTABLISHED:
            text = '{} {}'.format(
                text,
                '<span class="badge badge-primary">Routes: '
                '<i class="fas fa-arrow-circle-down"></i> {} '
                '<i class="fas fa-arrow-circle-up"></i> {}'
                '</span>'.format(self.received_prefix_count,
                                 self.advertised_prefix_count))

        return mark_safe(text)


class Community(CreatedUpdatedModel):
    name = models.CharField(max_length=128)
    value = CommunityField(max_length=50)
    type = models.CharField(max_length=50, choices=COMMUNITY_TYPE_CHOICES,
                            default=COMMUNITY_TYPE_INGRESS)
    comment = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'communities'
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('peering:community_details', kwargs={'pk': self.pk})

    def get_type_html(self):
        if self.type == COMMUNITY_TYPE_EGRESS:
            badge_type = 'badge-info'
            text = '<i class="fas fa-arrow-circle-up"></i> {}'.format(
                self.get_type_display().lower())
        elif self.type == COMMUNITY_TYPE_INGRESS:
            badge_type = 'badge-info'
            text = '<i class="fas fa-arrow-circle-down"></i> {}'.format(
                self.get_type_display().lower())
        else:
            badge_type = 'badge-secondary'
            text = '<i class="fas fa-ban"></i> unknown'

        return mark_safe('<span class="badge {}">{}</span>'.format(
            badge_type, text))

    def __str__(self):
        return self.name


class ConfigurationTemplate(CreatedUpdatedModel):
    name = models.CharField(max_length=128)
    template = models.TextField()
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('peering:configuration_template_details',
                       kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class DirectPeeringSession(BGPSession):
    local_asn = ASNField(default=0)
    relationship = models.CharField(
        max_length=50, choices=BGP_RELATIONSHIP_CHOICES,
        help_text='Relationship with the remote peer.')

    def get_absolute_url(self):
        return reverse('peering:direct_peering_session_details',
                       kwargs={'pk': self.pk})

    def get_relationship_html(self):
        if self.relationship == BGP_RELATIONSHIP_CUSTOMER:
            badge_type = 'badge-danger'
        elif self.relationship == BGP_RELATIONSHIP_PRIVATE_PEERING:
            badge_type = 'badge-success'
        elif self.relationship == BGP_RELATIONSHIP_TRANSIT_PROVIDER:
            badge_type = 'badge-primary'
        else:
            badge_type = 'badge-secondary'

        return mark_safe('<span class="badge {}">{}</span>'.format(
            badge_type, self.get_relationship_display()))

    def __str__(self):
        return '{} - AS{} - IP {}'.format(self.get_relationship_display(),
                                          self.autonomous_system.asn,
                                          self.ip_address)


class InternetExchange(CreatedUpdatedModel):
    peeringdb_id = models.PositiveIntegerField(blank=True, null=True)
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    ipv6_address = models.GenericIPAddressField(blank=True, null=True)
    ipv4_address = models.GenericIPAddressField(blank=True, null=True)
    comment = models.TextField(blank=True)
    configuration_template = models.ForeignKey('ConfigurationTemplate',
                                               blank=True, null=True,
                                               on_delete=models.SET_NULL)
    router = models.ForeignKey(
        'Router', blank=True, null=True, on_delete=models.SET_NULL)
    check_bgp_session_states = models.BooleanField(default=False)
    bgp_session_states_update = models.DateTimeField(blank=True, null=True)
    communities = models.ManyToManyField('Community', blank=True)

    logger = logging.getLogger('peering.manager.peering')

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('peering:internet_exchange_details', kwargs={'slug': self.slug})

    def get_peering_sessions_list_url(self):
        return reverse('peering:internet_exchange_peering_sessions',
                       kwargs={'slug': self.slug})

    def get_peer_list_url(self):
        return reverse('peering:internet_exchange_peers', kwargs={'slug': self.slug})

    def get_peering_sessions(self):
        return self.internetexchangepeeringsession_set.all()

    def get_autonomous_systems(self):
        autonomous_systems = []

        for session in self.internetexchangepeeringsession_set.all():
            if session.autonomous_system not in autonomous_systems:
                autonomous_systems.append(session.autonomous_system)

        return autonomous_systems

    def get_prefixes(self):
        return PeeringDB().get_prefixes_for_ix_network(self.peeringdb_id) or []

    def _generate_configuration_variables(self):
        peers6 = {}
        peers4 = {}

        # Sort peering sessions based on IP protocol version
        for session in self.internetexchangepeeringsession_set.all():
            ip_address = ipaddress.ip_address(session.ip_address)
            ipv6_max_prefixes = session.autonomous_system.ipv6_max_prefixes
            ipv4_max_prefixes = session.autonomous_system.ipv4_max_prefixes

            if ip_address.version == 6:
                if session.autonomous_system.asn not in peers6:
                    peers6[session.autonomous_system.asn] = {
                        'as_name': session.autonomous_system.name,
                        'max_prefixes': ipv6_max_prefixes or 0,
                        'sessions': [],
                    }

                peers6[session.autonomous_system.asn]['sessions'].append({
                    'ip_address': str(ip_address),
                    'password': session.password or False,
                    'enabled': session.enabled,
                })

            if ip_address.version == 4:
                if session.autonomous_system.asn not in peers4:
                    peers4[session.autonomous_system.asn] = {
                        'as_name': session.autonomous_system.name,
                        'max_prefixes': ipv4_max_prefixes or 0,
                        'sessions': [],
                    }

                peers4[session.autonomous_system.asn]['sessions'].append({
                    'ip_address': str(ip_address),
                    'password': session.password or False,
                    'enabled': session.enabled,
                })

        peering_groups = [
            {'ip_version': 6, 'peers': peers6},
            {'ip_version': 4, 'peers': peers4},
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

        return values

    def generate_configuration(self):
        # Load and render the template using Jinja2
        configuration_template = Template(self.configuration_template.template)
        return configuration_template.render(
            self._generate_configuration_variables())

    def get_available_peers(self):
        # Not linked to PeeringDB, cannot determine peers
        if not self.peeringdb_id:
            return None

        # Get the IX LAN we are belonging to
        api = PeeringDB()
        network_ixlan = api.get_ix_network(self.peeringdb_id)

        # Get all peering sessions currently existing
        existing_sessions = self.get_peering_sessions()
        ipv4_sessions = []
        ipv6_sessions = []
        for session in existing_sessions:
            ip = ipaddress.ip_address(session.ip_address)
            if ip.version == 6:
                ipv6_sessions.append(str(ip))
            elif ip.version == 4:
                ipv4_sessions.append(str(ip))
            else:
                self.logger.debug('peering session with strange ip: %s', ip)

        # Find all peers belonging to the same IX and order them by ASN
        # Exclude our own ASN and already existing sessions
        return PeerRecord.objects.all().filter(
            Q(network_ixlan__ix_id=network_ixlan.ixlan_id) &
            ~Q(network__asn=settings.MY_ASN) & (
                ~Q(network_ixlan__ipaddr6__in=ipv6_sessions) |
                ~Q(network_ixlan__ipaddr4__in=ipv4_sessions)
            )
        ).order_by('network__asn')

    def _import_peering_sessions(self, sessions=[], prefixes=[]):
        # No sessions or no prefixes, can't work with that
        if not sessions or not prefixes:
            return None

        # Values to be returned
        number_of_peering_sessions = 0
        number_of_autonomous_systems = 0
        ignored_autonomous_systems = []

        with transaction.atomic():
            # For each session check if the address fits in one of the prefixes
            for session in sessions:
                for prefix in prefixes:
                    # No point of checking if a session fits inside a prefix if
                    # they are not using the same IP version
                    if session['ip_address'].version is not prefix.version:
                        self.logger.debug('ip %s cannot fit in prefix %s (not same ip version) ignoring',
                                          str(session['ip_address']),
                                          str(prefix))
                        continue

                    self.logger.debug('checking if ip %s fits in prefix %s',
                                      str(session['ip_address']), str(prefix))

                    # If the address fits, create a new InternetExchangePeeringSession object
                    # and a new AutonomousSystem object if they does not exist
                    # already
                    if session['ip_address'] in prefix:
                        ip_address = str(session['ip_address'])
                        remote_asn = session['remote_asn']
                        self.logger.debug(
                            'ip %s fits in prefix %s', ip_address, str(prefix))

                        if not InternetExchangePeeringSession.does_exist(ip_address=ip_address,
                                                                         internet_exchange=self):
                            self.logger.debug(
                                'session %s with as%s does not exist',
                                ip_address, remote_asn)

                            # Grab the AS, create it if it does not exist in
                            # the database yet
                            autonomous_system = AutonomousSystem.does_exist(
                                remote_asn)
                            if not autonomous_system:
                                self.logger.debug(
                                    'as%s not present importing from peeringdb', remote_asn)
                                autonomous_system = AutonomousSystem.create_from_peeringdb(
                                    remote_asn)

                                # Do not count the AS if it does not have a
                                # PeeringDB record
                                if autonomous_system:
                                    self.logger.debug(
                                        'as%s created', remote_asn)
                                    number_of_autonomous_systems += 1
                                else:
                                    if remote_asn not in ignored_autonomous_systems:
                                        ignored_autonomous_systems.append(
                                            remote_asn)
                                    self.logger.debug(
                                        'could not create as%s, session %s ignored', remote_asn, ip_address)

                            # Only add a peering session if we were able to
                            # actually use the AS it is linked to
                            if autonomous_system:
                                self.logger.debug(
                                    'creating session %s', ip_address)
                                values = {
                                    'autonomous_system': autonomous_system,
                                    'internet_exchange': self,
                                    'ip_address': ip_address,
                                }
                                peering_session = InternetExchangePeeringSession(
                                    **values)
                                peering_session.save()
                                number_of_peering_sessions += 1
                                self.logger.debug(
                                    'session %s created', ip_address)
                        else:
                            self.logger.debug(
                                'session %s with as%s already exists',
                                ip_address, remote_asn)
                    else:
                        self.logger.debug('ip %s do not fit in prefix %s', str(
                            session['ip_address']), str(prefix))

        return (number_of_autonomous_systems, number_of_peering_sessions,
                ignored_autonomous_systems)

    def import_peering_sessions_from_router(self):
        log = 'ignoring peering session on {}, reason: "{}"'
        if not self.router:
            log = log.format(self.name.lower(), 'no router attached')
        elif not self.router.platform:
            log = log.format(self.name.lower(),
                             'router with unsupported platform')
        else:
            log = None

        # No point of discovering from router if platform is none or is not
        # supported.
        if log:
            self.logger.debug(log)
            return False

        # Build a list based on prefixes based on PeeringDB records
        prefixes = [ipaddress.ip_network(prefix['prefix'])
                    for prefix in self.get_prefixes()]
        # No prefixes found
        if not prefixes:
            self.logger.debug('no prefixes found for %s', self.name.lower())
            return None
        else:
            self.logger.debug('found %s prefixes (%s) for %s',
                              len(prefixes),
                              ', '.join([str(prefix) for prefix in prefixes]),
                              self.name.lower())

        # Gather all existing BGP sessions from the router connected to the IX
        bgp_sessions = self.router.get_napalm_bgp_neighbors()

        return self._import_peering_sessions(bgp_sessions, prefixes)

    def update_peering_session_states(self):
        # Check if we are able to get BGP details
        log = 'ignoring session states on {}, reason: "{}"'
        if not self.router:
            log = log.format(self.name.lower(), 'no router attached')
        elif not self.router.can_napalm_get_bgp_neighbors_detail():
            log = log.format(self.name.lower(),
                             'router with unsupported platform {}'.format(
                                 self.router.platform))
        elif not self.check_bgp_session_states:
            log = log.format(self.name.lower(), 'check disabled')
        else:
            log = None

        # If we cannot check for BGP details, don't do anything
        if log:
            self.logger.debug(log)
            return False

        # Get all BGP sessions detail
        bgp_neighbors_detail = self.router.get_napalm_bgp_neighbors_detail()
        with transaction.atomic():
            for vrf, as_details in bgp_neighbors_detail.items():
                for asn, sessions in as_details.items():
                    # Check BGP sessions found
                    for session in sessions:
                        ip_address = session['remote_address']
                        self.logger.debug(
                            'looking for session %s in %s', ip_address,
                            self.name.lower())

                        # Check if the BGP session is on this IX
                        peering_session = InternetExchangePeeringSession.does_exist(
                            internet_exchange=self, ip_address=ip_address)
                        if peering_session:
                            # Get the BGP state for the session
                            state = session['connection_state'].lower()
                            received = session['received_prefix_count']
                            advertised = session['advertised_prefix_count']
                            self.logger.debug(
                                'found session %s in %s with state %s',
                                ip_address, self.name.lower(), state)

                            # Update the BGP state of the session
                            if (peering_session.bgp_state == "Established"):
                                peering_session.last_state_established = timezone.localdate()

                            peering_session.bgp_state = state
                            peering_session.received_prefix_count = received
                            peering_session.advertised_prefix_count = advertised
                            peering_session.save()
                        else:
                            self.logger.debug(
                                'session %s in %s not found', ip_address,
                                self.name.lower())

            # Save last session states update
            self.bgp_session_states_update = timezone.now()
            self.save()

        return True

    def __str__(self):
        return self.name


class InternetExchangePeeringSession(BGPSession):
    internet_exchange = models.ForeignKey(
        'InternetExchange', on_delete=models.CASCADE)

    @staticmethod
    def does_exist(internet_exchange=None, autonomous_system=None,
                   ip_address=None):
        """
        Returns a InternetExchangePeeringSession object or None based on the positional
        arguments. If several objects are found, None is returned.

        TODO: the method must be reworked in order to have its proper return
        value if multiple objects are found.
        """
        # Filter based on fields that are not None
        filter = {}
        if internet_exchange:
            filter.update({'internet_exchange': internet_exchange})
        if autonomous_system:
            filter.update({'autonomous_system': autonomous_system})
        if ip_address:
            filter.update({'ip_address': ip_address})

        try:
            return InternetExchangePeeringSession.objects.get(**filter)
        except InternetExchangePeeringSession.DoesNotExist:
            return None
        except InternetExchangePeeringSession.MultipleObjectsReturned:
            return None

    @staticmethod
    def get_from_peeringdb_peer_record(peer_record, ip_version):
        internet_exchange = None
        peer_ixlan = None

        # If no peer record, no ASN or no IP address have been given, we
        # cannot do anything
        if (not peer_record or not peer_record.network.asn):
            return (None, False)

        # Find the Internet exchange given a NetworkIXLAN ID
        for ix in InternetExchange.objects.exclude(peeringdb_id__isnull=True):
            # Get the IXLAN corresponding to our network
            ixlan = NetworkIXLAN.objects.get(id=ix.peeringdb_id)
            # Get a potentially matching IXLAN
            peer_ixlan = NetworkIXLAN.objects.filter(
                id=peer_record.network_ixlan.id, ix_id=ixlan.ix_id)

            # IXLAN found lets get out
            if peer_ixlan:
                internet_exchange = ix
                break

        # Unable to find the Internet exchange, no point of going further
        if not internet_exchange:
            return (None, False)

        # Get the AS, create it if necessary
        autonomous_system = AutonomousSystem.create_from_peeringdb(
            peer_record.network.asn)

        if ip_version == 6:
            try:
                ipaddress.IPv6Address(peer_record.network_ixlan.ipaddr6)
            except ipaddress.AddressValueError:
                # IPv6 parsing failed, ignore the session
                return (None, False)
        elif ip_version == 4:
            try:
                ipaddress.IPv4Address(peer_record.network_ixlan.ipaddr4)
            except ipaddress.AddressValueError:
                # IPv4 parsing failed, ignore the session
                return (None, False)
        else:
            # Not a valid IP protocol version
            return (None, False)

        # Assume we are always using IPv6 unless told otherwise
        ip_address = (peer_record.network_ixlan.ipaddr4 if ip_version == 4 else
                      peer_record.network_ixlan.ipaddr6)

        # Try to get the session, in case it already exists
        session = InternetExchangePeeringSession.does_exist(
            autonomous_system=autonomous_system,
            internet_exchange=internet_exchange, ip_address=ip_address)

        # Session exists, nothing to do
        if session:
            return (session, False)

        # Create the session but do not save it
        session = InternetExchangePeeringSession(
            autonomous_system=autonomous_system,
            internet_exchange=internet_exchange, ip_address=ip_address)

        return (session, True)

    def get_absolute_url(self):
        return reverse('peering:internet_exchange_peering_session_details',
                       kwargs={'pk': self.pk})

    def __str__(self):
        return '{} - AS{} - IP {}'.format(self.internet_exchange.name,
                                          self.autonomous_system.asn,
                                          self.ip_address)


class Router(CreatedUpdatedModel):
    name = models.CharField(max_length=128)
    hostname = models.CharField(max_length=256)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES,
                                blank=True, help_text='The router platform, used to interact with it')
    comment = models.TextField(blank=True)

    logger = logging.getLogger('peering.manager.napalm')

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('peering:router_details', kwargs={'pk': self.pk})

    def can_napalm_get_bgp_neighbors_detail(self):
        return False if not self.platform else self.platform in [
            PLATFORM_EOS, PLATFORM_IOS, PLATFORM_IOSXR, PLATFORM_JUNOS
        ]

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
                'error while trying to connect to %s reason "%s"',
                self.hostname, e)
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
        alive = device.is_alive()
        closed = self.close_napalm_device(device)

        # Issue while opening or closing the connection
        if not opened or not closed or not alive:
            self.logger.error(
                'cannot connect to % s, napalm functions won\'t work',
                self.hostname)

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
                changes = None
                self.logger.debug(
                    'unable to merge configuration on %s reason "%s"',
                    self.hostname, e)
            except Exception as e:
                changes = None
                self.logger.debug(
                    'unable to merge configuration on %s error "%s"',
                    self.hostname, e)
            else:
                self.logger.debug(
                    'successfully merged configuration on %s', self.hostname)
            finally:
                closed = self.close_napalm_device(device)
                if not closed:
                    self.logger.debug(
                        'error while closing connection with %s',
                        self.hostname)

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
                        'ignored bgp neighbor %s in %s vrf on %s', ip, vrf,
                        self.hostname)
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

    def get_napalm_bgp_neighbors_detail(self):
        """
        Returns a list of dictionaries listing all BGP neighbors found on the
        router using NAPALM and there respective detail.

        If an error occurs or no BGP neighbors can be found, the returned list
        will be empty.
        """
        bgp_neighbors_detail = []

        device = self.get_napalm_device()
        opened = self.open_napalm_device(device)

        if opened:
            # Get all BGP neighbors on the router
            self.logger.debug(
                'getting bgp neighbors detail on %s', self.hostname)
            bgp_neighbors_detail = device.get_bgp_neighbors_detail()
            self.logger.debug('raw napalm output %s', bgp_neighbors_detail)
            self.logger.debug('found %s vrfs with bgp neighbors on %s', len(
                bgp_neighbors_detail), self.hostname)

            # Close connection to the device
            closed = self.close_napalm_device(device)
            if not closed:
                self.logger.debug(
                    'error while closing connection with %s', self.hostname)

        return bgp_neighbors_detail

    def __str__(self):
        return self.name
