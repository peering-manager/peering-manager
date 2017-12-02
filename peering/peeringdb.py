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

    def get_asn(self, asn):
        search = {'asn': asn}
        result = self.lookup(NAMESPACES['network'], search)

        if not result:
            return None

        return Object(result['data'][0])
