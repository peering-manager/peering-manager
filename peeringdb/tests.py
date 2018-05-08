from __future__ import unicode_literals

from django.test import TestCase
from django.utils import timezone

from .api import PeeringDB
from .models import Network, NetworkIXLAN


class PeeringDBTestCase(TestCase):
    def test_time_last_sync(self):
        api = PeeringDB()

        # Test when no sync has been done
        self.assertEqual(api.get_last_sync_time(), 0)

        # Test of sync record with no objects
        time_of_sync = timezone.now()
        api.record_last_sync(
            time_of_sync, {'added': 0, 'updated': 0, 'deleted': 0})
        self.assertEqual(api.get_last_sync_time(), 0)

        # Test of sync record with one object
        time_of_sync = timezone.now()
        api.record_last_sync(
            time_of_sync, {'added': 1, 'updated': 0, 'deleted': 0})
        self.assertEqual(api.get_last_sync_time(),
                         int(time_of_sync.timestamp()))

    def test_get_autonomous_system(self):
        api = PeeringDB()
        asn = 15169

        # Must not exist
        self.assertIsNone(api.get_autonomous_system(64500))

        # Using an API call (no cached data)
        autonomous_system = api.get_autonomous_system(asn)
        self.assertEqual(autonomous_system.asn, asn)

        # Save the data inside the cache
        details = {
            'id': autonomous_system.id,
            'asn': autonomous_system.asn,
            'name': autonomous_system.name,
        }
        network = Network(**details)
        network.save()

        # Using no API calls (cached data)
        autonomous_system = api.get_autonomous_system(asn)
        self.assertEqual(autonomous_system.asn, asn)

    def test_get_ix_network(self):
        api = PeeringDB()
        ix_network_id = 29146

        # Must not exist
        self.assertIsNone(api.get_ix_network(0))

        # Using an API call (no cached data)
        ix_network = api.get_ix_network(ix_network_id)
        self.assertEqual(ix_network.id, ix_network_id)

        # Save the data inside the cache
        details = {
            'id': ix_network.id,
            'asn': ix_network.asn,
            'name': ix_network.name,
            'ix_id': ix_network.ix_id,
            'ixlan_id': ix_network.ixlan_id,
        }
        network_ixlan = NetworkIXLAN(**details)
        network_ixlan.save()

        # Using no API calls (cached data)
        ix_network = api.get_ix_network(ix_network_id)
        self.assertEqual(ix_network.id, ix_network_id)

    def test_get_ix_networks_for_asn(self):
        api = PeeringDB()
        asn = 29467

        # Must not exist
        self.assertIsNone(api.get_ix_networks_for_asn(64500))

        known_ix_networks = [29146, 15321, 24292, 14658,
                             15210, 16774, 14657, 23162, 14659, 17707, 27863]
        found_ix_networks = []

        ix_networks = api.get_ix_networks_for_asn(asn)
        for ix_network in ix_networks:
            found_ix_networks.append(ix_network.id)

        self.assertEqual(sorted(found_ix_networks), sorted(known_ix_networks))

    def test_get_prefixes_for_ix_network(self):
        api = PeeringDB()
        ix_network_id = 29146

        # Must be empty
        self.assertFalse(api.get_prefixes_for_ix_network(0))

        known_prefixes = ['2001:7f8:1::/64', '80.249.208.0/21']
        found_prefixes = []

        ix_prefixes = api.get_prefixes_for_ix_network(ix_network_id)
        for ix_prefix in ix_prefixes:
            found_prefixes.append(ix_prefix['prefix'])

        self.assertEqual(sorted(found_prefixes), sorted(known_prefixes))

    def test_get_peers_for_ix(self):
        api = PeeringDB()
        ix_id = 1019

        # Must not be found
        self.assertIsNone(api.get_peers_for_ix(0))

        # Must have some peers
        self.assertEqual(len(api.get_peers_for_ix(ix_id)), 8)
