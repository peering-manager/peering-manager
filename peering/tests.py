from __future__ import unicode_literals

import ipaddress

from django.test import TestCase

from .models import AutonomousSystem, InternetExchange, Router


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


class InternetExchangeTesCase(TestCase):
    def test_import_peering_sessions(self):
        # Expected results
        expected = [
            # First case
            (1, 1),
            # Second case
            (0, 1),
            # Third case
            (0, 1),
            # Fourth case
            (0, 0),
        ]

        session_lists = [
            # First case, one new session with one new AS
            [
                {
                    'ip_address': ipaddress.ip_address('2001:db8::1'),
                    'remote_asn': 29467,
                }
            ],
            # Second case, one new session with one known AS
            [
                {
                    'ip_address': ipaddress.ip_address('192.168.0.1'),
                    'remote_asn': 29467,
                }
            ],
            # Third case, new IPv4 session on another IX but with an IP that
            # has already been used
            [
                {
                    'ip_address': ipaddress.ip_address('192.168.0.1'),
                    'remote_asn': 29467,
                }
            ],
            # Fourth case, new IPv4 session with IPv6 prefix
            [
                {
                    'ip_address': ipaddress.ip_address('192.168.2.1'),
                    'remote_asn': 29467,
                }
            ],
        ]

        prefix_lists = [
            # First case
            [ipaddress.ip_network('2001:db8::/64')],
            # Second case
            [ipaddress.ip_network('192.168.0.0/24')],
            # Third case
            [ipaddress.ip_network('192.168.0.0/24')],
            # Fourth case
            [ipaddress.ip_network('2001:db8::/64')],
        ]

        # Run test cases
        for i in range(0, len(expected)):
            ixp = InternetExchange.objects.create(name='Test {}'.format(i),
                                                  slug='test_{}'.format(i))
            self.assertEqual(expected[i],
                             ixp._import_peering_sessions(session_lists[i],
                                                          prefix_lists[i]))
            self.assertEqual(expected[i][1], ixp.get_peering_sessions_count())


class RouterTestCase(TestCase):
    def test_napalm_bgp_neighbors_to_peer_list(self):
        # Expected results
        expected = [0, 0, 1, 2, 3, 2, 2]

        napalm_dicts_list = [
            # If None or empty dict passed, returned value must be empty list
            None,
            {},
            # List size must match peers number including VRFs
            {'global': {'peers': {'192.168.0.1': {'remote_as': 64500}}}},
            {'global': {'peers': {'192.168.0.1': {'remote_as': 64500}}},
             'vrf': {'peers': {'192.168.1.1': {'remote_as': 64501}}}},
            {'global': {'peers': {'192.168.0.1': {'remote_as': 64500}}},
             'vrf0': {'peers': {'192.168.1.1': {'remote_as': 64501}}},
             'vrf1': {'peers': {'192.168.2.1': {'remote_as': 64502}}}},
            # If peer does not have remote_as field, it must be ignored
            {'global': {'peers': {'192.168.0.1': {'remote_as': 64500}}},
             'vrf0': {'peers': {'192.168.1.1': {'remote_as': 64501}}},
             'vrf1': {'peers': {'192.168.2.1': {'not_valid': 64502}}}},
            # If an IP address appears more than one time, only the first
            # occurence  must be retained
            {'global': {'peers': {'192.168.0.1': {'remote_as': 64500}}},
             'vrf0': {'peers': {'192.168.1.1': {'remote_as': 64501}}},
             'vrf1': {'peers': {'192.168.1.1': {'remote_as': 64502}}}},
        ]

        # Create a router
        router = Router.objects.create(name='test',
                                       hostname='test.example.com',
                                       platform=Router.PLATFORM_JUNOS)

        # Run test cases
        for i in range(0, len(expected)):
            self.assertEqual(expected[i], len(
                router._napalm_bgp_neighbors_to_peer_list(napalm_dicts_list[i])))
