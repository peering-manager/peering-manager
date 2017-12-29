from __future__ import unicode_literals

import json
import logging
import requests

from django.conf import settings
from django.utils import timezone

from .models import Network, Synchronization


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

    def record_last_sync(self, time, number_of_objects):
        """
        Save the last synchronization details (number of objects and time) for
        later use (and logs).
        """
        # Save the last sync time only if objects were retrieved
        if number_of_objects > 0:
            values = {
                'time': time,
                'number_of_objects': number_of_objects,
            }

            last_sync = Synchronization(**values)
            last_sync.save()

            self.logger.debug('synchronizated %s objects at %s',
                              number_of_objects, last_sync.time)

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
        """
        # Set time of sync
        number_of_objects_synced = 0
        time_of_sync = timezone.now()

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
                    self.logger.debug(
                        'deleted as%s from peeringdb', peeringdb_network.asn)
                else:
                    # Update the fields
                    for key, value in new_values.items():
                        setattr(network, key, value)
                    network.save()
                    self.logger.debug(
                        'updated as%s from peeringdb', peeringdb_network.asn)
            except Network.DoesNotExist:
                if not is_deleted:
                    # Create a new Network object
                    network = Network(**new_values)
                    network.save()
                    self.logger.debug(
                        'created as%s from peeringdb', peeringdb_network.asn)

            if not is_deleted:
                number_of_objects_synced += 1

        # Save the last sync time
        self.record_last_sync(time_of_sync, number_of_objects_synced)

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
        Returns the IX network for a given ID.
        """
        search = {'id': ix_network_id}
        result = self.lookup(
            NAMESPACES['network_internet_exchange_lan'], search)

        if not result:
            return None

        return Object(result['data'][0])

    def get_ix_networks_for_asn(self, asn):
        """
        Returns a list of all IX networks an AS is connected to.
        """
        search = {'asn': asn}
        result = self.lookup(
            NAMESPACES['network_internet_exchange_lan'], search)

        if not result:
            return None

        ix_networks = []
        for ix_network in result['data']:
            ix_networks.append(Object(ix_network))

        return ix_networks

    def get_peers_for_ix(self, ix_id):
        """
        Returns a dict with details for peers for the IX corresponding to the
        given ID. This function can take some time to execute due to the amount
        of peers on the IX.
        """
        search = {'ix_id': ix_id}
        result = self.lookup(
            NAMESPACES['network_internet_exchange_lan'], search)

        if not result:
            return None

        peers = []
        for data in result['data']:
            peer = Object(data)

            # Ignore our own ASN
            if peer.asn == settings.MY_ASN:
                continue

            # Get more details about the current network
            network = self.get_autonomous_system(peer.asn)

            # Package all gathered details
            peers.append({
                'asn': peer.asn,
                'name': network.name,
                'irr_as_set': network.irr_as_set,
                'ipv6_max_prefixes': network.info_prefixes6,
                'ipv4_max_prefixes': network.info_prefixes4,
                'ipv6_address': peer.ipaddr6,
                'ipv4_address': peer.ipaddr4,

            })

        return peers
