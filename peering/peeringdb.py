from __future__ import unicode_literals

import json
import requests

from django.conf import settings


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

    This will probably be modified or even deleted when we will start using the
    existing library.
    """

    def lookup(self, namespace, search):
        """
        Send a get request to the API given a namespace and some parameters.
        """
        # Enforce trailing slash and add namespace
        api_url = settings.PEERINGDB_API.strip('/') + '/' + namespace

        # Check if the depth param is provided, add it if not
        if 'depth' not in search:
            search['depth'] = 1

        # Make the request
        response = requests.get(api_url, params=search)

        # If not OK just give us none
        if response.status_code != 200:
            return None

        return response.json()

    def get_autonomous_system(self, asn):
        search = {'asn': asn}
        result = self.lookup(NAMESPACES['network'], search)

        if not result:
            return None

        return Object(result['data'][0])

    def get_ix_network(self, ix_network_id):
        search = {'id': ix_network_id}
        result = self.lookup(
            NAMESPACES['network_internet_exchange_lan'], search)

        if not result:
            return None

        return Object(result['data'][0])

    def get_ix_networks_for_asn(self, asn):
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
        search = {'ix_id': ix_id, 'depth': 0}
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
                'as_set': network.irr_as_set,
                'ipv6_max_prefixes': network.info_prefixes6,
                'ipv4_max_prefixes': network.info_prefixes4,
                'ipv6_address': peer.ipaddr6,
                'ipv4_address': peer.ipaddr4,

            })

        return peers
