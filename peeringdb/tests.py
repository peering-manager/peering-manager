from __future__ import unicode_literals

from django.test import TestCase
from django.utils import timezone

from .api import PeeringDB
from .models import Network


class PeeringDBTestCase(TestCase):
    def test_time_last_sync(self):
        api = PeeringDB()

        # Test when no sync has been done
        self.assertEqual(api.get_last_sync_time(), 0)

        # Test of sync record with no objects
        time_of_sync = timezone.now()
        api.record_last_sync(time_of_sync, 0)
        self.assertEqual(api.get_last_sync_time(), 0)

        # Test of sync record with one object
        time_of_sync = timezone.now()
        api.record_last_sync(time_of_sync, 1)
        self.assertEqual(api.get_last_sync_time(),
                         int(time_of_sync.timestamp()))

    def test_get_autonomous_system(self):
        api = PeeringDB()
        asn = 15169

        # Using an API call (no cached data)
        autonomous_system = api.get_autonomous_system(asn)
        self.assertEqual(autonomous_system.asn, asn)

        # Save the data inside the cache
        details = {
            'asn': autonomous_system.asn,
            'name': autonomous_system.name,
        }
        network = Network(**details)
        network.save()

        # Using without API call (cached data)
        autonomous_system = api.get_autonomous_system(asn)
        self.assertEqual(autonomous_system.asn, asn)

    def test_get_ix_network(self):
        api = PeeringDB()
        ix_network_id = 29146

        known_ix_network_name = 'AMS-IX'
        found_ix_network = api.get_ix_network(ix_network_id)
        self.assertEqual(found_ix_network.name, known_ix_network_name)

    def test_get_ix_networks_for_asn(self):
        api = PeeringDB()
        asn = 29467

        known_ix_networks = [29146, 15321, 24292, 14658,
                             15210, 16774, 14657, 23162, 14659, 17707, 27863]
        found_ix_networks = []

        ix_networks = api.get_ix_networks_for_asn(asn)
        for ix_network in ix_networks:
            found_ix_networks.append(ix_network.id)

        self.assertEqual(sorted(found_ix_networks), sorted(known_ix_networks))
