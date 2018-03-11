from __future__ import unicode_literals

from django.test import TestCase

from .models import AutonomousSystem, Router


class AutonomousSystemTestCase(TestCase):
    def test_does_exist(self):
        asn = 29467

        # AS should not exist
        autonomous_system = AutonomousSystem.does_exist(asn)
        self.assertEqual(None, autonomous_system)

        # Create the AS
        new_as = AutonomousSystem.objects.create(asn=asn,
                                                 name='LuxNetwork S.A.')

        # AS must exist
        autonomous_system = AutonomousSystem.does_exist(asn)
        self.assertEqual(asn, new_as.asn)

    def test_create_from_peeringdb(self):
        asn = 29467

        # Must not exist at first
        self.assertEqual(None, AutonomousSystem.does_exist(asn))

        # Create the AS
        autonomous_system1 = AutonomousSystem.create_from_peeringdb(asn)
        self.assertEqual(asn, autonomous_system1.asn)

        # Must exist now
        self.assertEqual(asn, AutonomousSystem.does_exist(asn).asn)

        # Must not rise error, just return the AS
        autonomous_system2 = AutonomousSystem.create_from_peeringdb(asn)
        self.assertEqual(asn, autonomous_system2.asn)

        # Must exist now also
        self.assertEqual(asn, AutonomousSystem.does_exist(asn).asn)


class RouterTestCase(TestCase):
    def test_napalm_bgp_neighbors_to_peer_list(self):
        dict_0 = None
        dict_1 = {}
        dict_2 = {'global': {'peers': {'192.168.0.1': {'remote_as': 64500}}}}
        dict_3 = {'global': {'peers': {'192.168.0.1': {'remote_as': 64500}}},
                  'vrf': {'peers': {'192.168.1.1': {'remote_as': 64501}}}}
        dict_4 = {'global': {'peers': {'192.168.0.1': {'remote_as': 64500}}},
                  'vrf0': {'peers': {'192.168.1.1': {'remote_as': 64501}}},
                  'vrf1': {'peers': {'192.168.2.1': {'remote_as': 64502}}}}
        dict_5 = {'global': {'peers': {'192.168.0.1': {'remote_as': 64500}}},
                  'vrf0': {'peers': {'192.168.1.1': {'remote_as': 64501}}},
                  'vrf1': {'peers': {'192.168.2.1': {'remote_an': 64502}}}}
        dict_6 = {'global': {'peers': {'192.168.0.1': {'remote_as': 64500}}},
                  'vrf0': {'peers': {'192.168.1.1': {'remote_as': 64501}}},
                  'vrf1': {'peers': {'192.168.1.1': {'remote_as': 64502}}}}

        # Create a router
        router = Router.objects.create(name='test',
                                       hostname='test.example.com',
                                       platform=Router.PLATFORM_JUNOS)

        # If None or empty dict passed, returned value must be empty list
        self.assertEqual(
            0, len(router._napalm_bgp_neighbors_to_peer_list(dict_0)))
        self.assertEqual(
            0, len(router._napalm_bgp_neighbors_to_peer_list(dict_1)))
        # List size must match peers number including VRFs
        self.assertEqual(
            1, len(router._napalm_bgp_neighbors_to_peer_list(dict_2)))
        self.assertEqual(
            2, len(router._napalm_bgp_neighbors_to_peer_list(dict_3)))
        self.assertEqual(
            3, len(router._napalm_bgp_neighbors_to_peer_list(dict_4)))
        # If peer does not have remote_as field, it must be ignored
        self.assertEqual(
            2, len(router._napalm_bgp_neighbors_to_peer_list(dict_5)))
        # If an IP address appears more than one time, only the first occurence
        # must be retained
        self.assertEqual(
            2, len(router._napalm_bgp_neighbors_to_peer_list(dict_6)))
