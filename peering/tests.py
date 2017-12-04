from __future__ import unicode_literals

from django.test import TestCase

from .peeringdb import PeeringDB


class PeeringDBTestCase(TestCase):
    def test_get_autonomous_system(self):
        api = PeeringDB()
        asn = 15169

        autonomous_system = api.get_autonomous_system(asn)
        self.assertEqual(autonomous_system.asn, asn)

    def test_get_ix_networks_for_asn(self):
        api = PeeringDB()
        asn = 29467

        known_ix_networks = [29146, 15321, 24292, 14658,
                             15210, 16774, 14657, 23162, 14659, 17707, 27863]
        found_ix_networks = []

        ix_networks = api.get_ix_networks_for_asn(asn)
        for ix_network in ix_networks:
            found_ix_networks.append(ix_network.id)

        self.assertEqual(found_ix_networks, known_ix_networks)

    def test_get_internet_exchange(self):
        api = PeeringDB()
        ix_id = 359

        known_ix_name = 'France-IX Paris'
        found_ix = api.get_internet_exchange_by_id(ix_id)
        self.assertEqual(found_ix.name, known_ix_name)
