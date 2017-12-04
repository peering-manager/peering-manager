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
    def __init__(self, data):
        self.__dict__ = json.loads(json.dumps(data))

    def __str__(self):
        return str(self.__dict__)


class PeeringDB(object):
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

        if response.status_code != 200:
            return None

        return response.json()

    def get_autonomous_system(self, asn):
        search = {'asn': asn}
        result = self.lookup(NAMESPACES['network'], search)

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

    def get_internet_exchange_by_id(self, ix_network_id):
        search = {'id': ix_network_id}
        result = self.lookup(
            NAMESPACES['internet_exchange'], search)

        if not result:
            return None

        return Object(result['data'][0])
