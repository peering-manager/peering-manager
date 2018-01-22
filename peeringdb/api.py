from __future__ import unicode_literals

import json
import logging
import requests

from django.db import transaction
from django.conf import settings
from django.utils import timezone

from .models import Network, NetworkIXLAN, Synchronization


NAMESPACES = {
    'facility': 'fac',
    'internet_exchange': 'ix',
    'internet_exchange_facility': 'ixfac',
    'internet_exchange_lan': 'ixlan',
    'internet_exchange_prefix': 'ixpfx',
    'network': 'net',
    'network_facility': 'netfac',
    'network_internet_exchange_lan': 'netixlan',
    'organization': 'org',
    'network_contact': 'poc',
}


class Object(object):
    """
    This is a class used to load JSON data into class fields for easier use.
    """

    def __init__(self, data):
        self.__dict__ = json.loads(json.dumps(data))

    def __str__(self):
        return str(self.__dict__)


class PeeringDB(object):
    """
    Class used to interact with the PeeringDB API.
    """
    logger = logging.getLogger('peering.manager.peeringdb')

    def lookup(self, namespace, search):
        """
        Sends a get request to the API given a namespace and some parameters.
        """
        # Enforce trailing slash and add namespace
        api_url = settings.PEERINGDB_API.strip('/') + '/' + namespace

        # Check if the depth param is provided, add it if not
        if 'depth' not in search:
            search['depth'] = 1

        # Make the request
        self.logger.debug('calling api: %s | %s', api_url, search)
        response = requests.get(api_url, params=search)

        return response.json() if response.status_code == 200 else None

    def record_last_sync(self, time, objects_changes):
        """
        Save the last synchronization details (number of objects and time) for
        later use (and logs).
        """
        number_of_changes = objects_changes['added'] + \
            objects_changes['updated'] + objects_changes['deleted']

        # Save the last sync time only if objects were retrieved
        if number_of_changes > 0:
            values = {
                'time': time,
                'added': objects_changes['added'],
                'updated': objects_changes['updated'],
                'deleted': objects_changes['deleted'],
            }

            last_sync = Synchronization(**values)
            last_sync.save()

            self.logger.debug('synchronizated %s objects at %s',
                              number_of_changes, last_sync.time)

    def get_last_sync_time(self):
        """
        Return the last time of synchronization based on the latest record.
        The time is returned as an integer UNIX timestamp.
        """
        # Assume first sync
        last_sync_time = 0
        try:
            # If a sync has already been performed, get the last of it given
            # its time
            last_sync = Synchronization.objects.latest('time')
            last_sync_time = last_sync.time.timestamp()
        except Synchronization.DoesNotExist:
            pass

        return int(last_sync_time)

    def get_all_networks(self, last_sync):
        """
        Synchronizes all the Network objects of the PeeringDB to the local
        database. This function is meant to be run regularly to update the
        local database with the latest changes.

        If a Network already exists locally it will be updated and no new entry
        will be created.

        If a Network is marked as deleted in the PeeringDB, it will be locally
        deleted.

        This function returns the number of objects that have been successfully
        synchronized to the local database.
        """
        objects_added = 0
        objects_updated = 0
        objects_deleted = 0

        # Get all network changes since the last sync
        search = {'since': last_sync, 'depth': 0}
        result = self.lookup(NAMESPACES['network'], search)

        if not result:
            return None

        for data in result['data']:
            peeringdb_network = Object(data)

            # Ignore our own AS
            if peeringdb_network.asn == settings.MY_ASN:
                continue

            # Has the network been deleted?
            is_deleted = peeringdb_network.status == 'deleted'

            new_values = {
                'id': peeringdb_network.id,
                'asn': peeringdb_network.asn,
                'name': peeringdb_network.name,
                'irr_as_set': peeringdb_network.irr_as_set,
                'info_prefixes6': peeringdb_network.info_prefixes6,
                'info_prefixes4': peeringdb_network.info_prefixes4,
            }

            try:
                # Get the existing Network object
                network = Network.objects.get(asn=peeringdb_network.asn)

                # If the network has been deleted in the source, remove it from
                # the local database too
                if is_deleted:
                    network.delete()
                    objects_deleted += 1
                    self.logger.debug(
                        'deleted as%s from peeringdb', peeringdb_network.asn)
                else:
                    # Update the fields
                    for key, value in new_values.items():
                        setattr(network, key, value)
                    network.save()
                    objects_updated += 1
                    self.logger.debug(
                        'updated as%s from peeringdb', network.asn)
            except Network.DoesNotExist:
                if not is_deleted:
                    # Create a new Network object
                    network = Network(**new_values)
                    network.save()
                    objects_added += 1
                    self.logger.debug(
                        'created as%s from peeringdb', network.asn)

        return (objects_added, objects_updated, objects_deleted)

    def get_all_network_ixlans(self, last_sync):
        """
        Synchronizes all the NetworkIXLAN objects of the PeeringDB to the local
        database. This function is meant to be run regularly to update the
        local database with the latest changes.

        If a NetworkIXLAN already exists locally it will be updated and no new
        entry will be created.

        If a NetworkIXLAN is marked as deleted in the PeeringDB, it will be
        locally deleted.

        This function returns the number of objects that have been successfully
        synchronized to the local database.
        """
        objects_added = 0
        objects_updated = 0
        objects_deleted = 0

        # Get all network IX LAN changes since the last sync
        search = {'since': last_sync, 'depth': 0}
        result = self.lookup(
            NAMESPACES['network_internet_exchange_lan'], search)

        if not result:
            return None

        for data in result['data']:
            peeringdb_network_ixlan = Object(data)

            # Has the network IX LAN been deleted?
            is_deleted = peeringdb_network_ixlan.status == 'deleted'

            new_values = {
                'id': peeringdb_network_ixlan.id,
                'asn': peeringdb_network_ixlan.asn,
                'name': peeringdb_network_ixlan.name,
                'ipaddr6': peeringdb_network_ixlan.ipaddr6,
                'ipaddr4': peeringdb_network_ixlan.ipaddr4,
                'is_rs_peer': peeringdb_network_ixlan.is_rs_peer,
                'ix_id': peeringdb_network_ixlan.ix_id,
            }

            try:
                # Get the existing NetworkIXLAN object
                network_ixlan = NetworkIXLAN.objects.get(
                    id=peeringdb_network_ixlan.id)

                # If the network IX LAN has been deleted in the source, remove
                # it from the local database too
                if is_deleted:
                    network_ixlan.delete()
                    objects_deleted += 1
                    self.logger.debug(
                        'deleted network ixlan #%s from peeringdb', peeringdb_network_ixlan.id)
                else:
                    # Update the fields
                    for key, value in new_values.items():
                        setattr(network_ixlan, key, value)
                    network_ixlan.save()
                    objects_updated += 1
                    self.logger.debug(
                        'updated network ixlan #%s from peeringdb', network_ixlan.id)
            except NetworkIXLAN.DoesNotExist:
                if not is_deleted:
                    # Create a new NetworkIXLAN object
                    network_ixlan = NetworkIXLAN(**new_values)
                    network_ixlan.save()
                    objects_added += 1
                    self.logger.debug(
                        'created network ixlan #%s from peeringdb', network_ixlan.id)

        return (objects_added, objects_updated, objects_deleted)

    def update_local_database(self, last_sync):
        # Set time of sync
        time_of_sync = timezone.now()

        # Make a single transaction, avoid too much database commits (poor
        # speed) and fail the whole synchronization if something goes wrong
        with transaction.atomic():
            # Try to sync objects
            networks_changes = self.get_all_networks(last_sync)
            network_ixlans_changes = self.get_all_network_ixlans(last_sync)

        objects_changes = {
            'added': networks_changes[0] + network_ixlans_changes[0],
            'updated': networks_changes[1] + network_ixlans_changes[1],
            'deleted': networks_changes[2] + network_ixlans_changes[2],
        }

        # Save the last sync time
        self.record_last_sync(time_of_sync, objects_changes)

    def get_autonomous_system(self, asn):
        """
        Return an AS (and its details) given its ASN. The result can come from
        the local database (cache built with the peeringdb_sync command). If
        the AS details are not found in the local database, they will be
        fetched online which will take more time.
        """
        try:
            # Try to get from cached data
            network = Network.objects.get(asn=asn)
        except Network.DoesNotExist:
            # If no cached data found, query the API
            search = {'asn': asn}
            result = self.lookup(NAMESPACES['network'], search)

            if not result:
                return None

            network = Object(result['data'][0])

        return network

    def get_ix_network(self, ix_network_id):
        """
        Return an IX networks (and its details) given its ID. The result can
        come from the local database (cache built with the peeringdb_sync
        command). If the IX network is not found in the local database, it will
        be fetched online which will take more time.
        """
        try:
            # Try to get from cached data
            network_ixlan = NetworkIXLAN.objects.get(id=ix_network_id)
        except NetworkIXLAN.DoesNotExist:
            # If no cached data found, query the API
            search = {'id': ix_network_id}
            result = self.lookup(
                NAMESPACES['network_internet_exchange_lan'], search)

            if not result:
                return None

            network_ixlan = Object(result['data'][0])

        return network_ixlan

    def get_ix_networks_for_asn(self, asn):
        """
        Returns a list of all IX networks an AS is connected to.
        """
        # Try to get from cached data
        network_ixlans = NetworkIXLAN.objects.filter(asn=asn)

        # If nothing found in cache, try to fetch data online
        if not network_ixlans:
            search = {'asn': asn}
            result = self.lookup(
                NAMESPACES['network_internet_exchange_lan'], search)

            if not result:
                return None

            network_ixlans = []
            for ix_network in result['data']:
                network_ixlans.append(Object(ix_network))

        return network_ixlans

    def get_peers_for_ix(self, ix_id):
        """
        Returns a dict with details for peers for the IX corresponding to the
        given ID. This function try to leverage the use of local database
        caching. If the cache is not built it can take some time to execute due
        to the amount of peers on the IX which increases the number of API
        calls to be made.
        """
        # Try to get from cached data
        network_ixlans = NetworkIXLAN.objects.filter(ix_id=ix_id)

        # If nothing found in cache, try to fetch data online
        if not network_ixlans:
            search = {'ix_id': ix_id}
            result = self.lookup(
                NAMESPACES['network_internet_exchange_lan'], search)

            if not result:
                return None

            network_ixlans = []
            for data in result['data']:
                network_ixlans.append(Object(data))

        # List potential peers
        peers = []
        for network_ixlan in network_ixlans:
            # Ignore our own ASN
            if network_ixlan.asn == settings.MY_ASN:
                continue

            # Get more details about the current network
            network = self.get_autonomous_system(network_ixlan.asn)

            # Package all gathered details
            peers.append({
                'network': network,
                'network_ixlan': network_ixlan,
            })

        return peers
