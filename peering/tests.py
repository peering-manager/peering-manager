from __future__ import unicode_literals

import ipaddress

from django.test import TestCase
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from .constants import (COMMUNITY_TYPE_INGRESS, COMMUNITY_TYPE_EGRESS,
                        PLATFORM_JUNOS)
from .models import (AutonomousSystem, Community, InternetExchange,
                     PeeringSession, Router)

from utils.tests import ViewTestCase


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

        # Illegal ASN
        self.assertIsNone(AutonomousSystem.create_from_peeringdb(64500))

        # Must not exist at first
        self.assertIsNone(AutonomousSystem.does_exist(asn))

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

    def test_sync_with_peeringdb(self):
        # Create legal AS to sync with PeeringDB
        asn = 29467
        autonomous_system = AutonomousSystem.create_from_peeringdb(asn)
        self.assertEqual(asn, autonomous_system.asn)
        self.assertTrue(autonomous_system.sync_with_peeringdb())

        # Create illegal AS to fail sync with PeeringDB
        asn = 64500
        autonomous_system = AutonomousSystem.objects.create(asn=asn,
                                                            name='Test')
        self.assertEqual(asn, autonomous_system.asn)
        self.assertFalse(autonomous_system.sync_with_peeringdb())

    def test__str__(self):
        asn = 64500
        name = 'Test'
        expected = 'AS{} - {}'.format(asn, name)
        autonomous_system = AutonomousSystem.objects.create(asn=asn, name=name)

        self.assertEqual(expected, str(autonomous_system))


class AutonomousSystemViewsTestCase(ViewTestCase):
    def setUp(self):
        super(AutonomousSystemViewsTestCase, self).setUp()

        self.asn = 29467
        self.as_name = 'LuxNetwork S.A.'
        self.autonomous_system = AutonomousSystem.objects.create(
            asn=self.asn, name=self.as_name)

    def test_as_list_view(self):
        response = self.client.get(reverse('peering:as_list'))
        self.assertEqual(response.status_code, 200)

    def test_as_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:as_add'))
        self.assertEqual(response.status_code, 302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        response = self.client.get(reverse('peering:as_add'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create')

        # Try to create an object with valid data
        as_to_create = {
            'asn': 64500,
            'name': 'as-created',
        }
        response = self.client.post(reverse('peering:as_add'), as_to_create)
        self.assertEqual(response.status_code, 302)
        self.does_object_exist(AutonomousSystem, as_to_create)

        # Try to create an object with invalid data
        as_not_to_create = {
            'asn': 64501,
        }
        response = self.client.post(reverse('peering:as_add'),
                                    as_not_to_create)
        self.assertEqual(response.status_code, 200)
        self.does_object_not_exist(AutonomousSystem, as_not_to_create)

    def test_as_import_view(self):
        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:as_import'))
        self.assertEqual(response.status_code, 302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        response = self.client.get(reverse('peering:as_import'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Import')

        # Try to import an object with valid data
        as_to_import = {
            'csv': '''asn,name,irr_as_set,ipv6_max_prefixes,ipv4_max_prefixes,comment
                      64500,as-created,,,,''',
        }
        response = self.client.post(reverse('peering:as_import'), as_to_import)
        self.assertEqual(response.status_code, 302)
        self.does_object_exist(AutonomousSystem, {'asn': 64500})

        # Try to create an object with invalid data
        as_not_to_import = {
            'csv': '''asn,name,irr_as_set,ipv6_max_prefixes,ipv4_max_prefixes,comment
                      64501,as-not-created,,,,''',
        }
        response = self.client.post(reverse('peering:as_import'),
                                    as_not_to_import)
        self.assertEqual(response.status_code, 302)
        self.does_object_exist(AutonomousSystem, {'asn': 64501})

    def test_as_import_from_peeringdb_view(self):
        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:as_import_from_peeringdb'))
        self.assertEqual(response.status_code, 302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        response = self.client.get(reverse('peering:as_import_from_peeringdb'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PeeringDB')

        # Using a wrong AS number
        response = self.client.post(
            reverse('peering:as_import_from_peeringdb'), {'asn': 64500})
        self.assertEqual(response.status_code, 200)
        self.does_object_not_exist(AutonomousSystem, {'asn': 64500})

        # Using an existing AS, status should be 302
        response = self.client.get(reverse('peering:as_import_from_peeringdb'),
                                   {'asn': self.asn})
        self.assertEqual(response.status_code, 200)
        self.does_object_exist(AutonomousSystem, {'asn': self.asn})

    def test_as_details_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('peering:as_details'))

        # Using a wrong AS number, status should be 404 not found
        response = self.client.get(reverse('peering:as_details',
                                           kwargs={'asn': 64500}))
        self.assertEqual(response.status_code, 404)

        # Using an existing AS, status should be 200 and the name of the AS
        # should be somewhere in the HTML code
        response = self.client.get(self.autonomous_system.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'LuxNetwork')

    def test_as_edit_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('peering:as_edit'))

        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:as_edit',
                                           kwargs={'asn': self.asn}))
        self.assertEqual(response.status_code, 302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        response = self.client.get(reverse('peering:as_edit',
                                           kwargs={'asn': self.asn}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Update')

        # Still authenticated, wrong AS should be 404 not found
        response = self.client.get(reverse('peering:as_edit',
                                           kwargs={'asn': 64500}))
        self.assertEqual(response.status_code, 404)

    def test_as_delete_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('peering:as_delete'))

        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:as_delete',
                                           kwargs={'asn': self.asn}))
        self.assertEqual(response.status_code, 302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        response = self.client.get(reverse('peering:as_delete',
                                           kwargs={'asn': self.asn}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirm')

        # Still authenticated, wrong AS should be 404 not found
        response = self.client.get(reverse('peering:as_delete',
                                           kwargs={'asn': 64500}))
        self.assertEqual(response.status_code, 404)

    def test_as_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:as_bulk_delete'))
        self.assertEqual(response.status_code, 302)

    def test_as_peeringdb_sync_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('peering:as_peeringdb_sync'))

        # Using a wrong AS number, status should be 404 not found
        response = self.client.get(reverse('peering:as_peeringdb_sync',
                                           kwargs={'asn': 64500}))
        self.assertEqual(response.status_code, 404)

        # Using an existing AS, status should be 302
        response = self.client.get(reverse('peering:as_peeringdb_sync',
                                           kwargs={'asn': self.asn}))
        self.assertEqual(response.status_code, 302)

    def test_as_peering_sessions_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('peering:as_peering_sessions'))

        # Using a wrong AS number, status should be 404 not found
        response = self.client.get(reverse('peering:as_peering_sessions',
                                           kwargs={'asn': 64500}))
        self.assertEqual(response.status_code, 404)

        # Using an existing AS, status should be 200
        response = self.client.get(
            self.autonomous_system.get_peering_sessions_list_url())
        self.assertEqual(response.status_code, 200)


class CommunityTestCase(TestCase):
    def test_create(self):
        community_list = [
            {
                'name': 'Test',
                'value': '64500:1',
                'type': None,
                'str': 'Test',
            },
            {
                'name': 'Test',
                'value': '64500:1',
                'type': COMMUNITY_TYPE_EGRESS,
                'str': 'Test',
            },
        ]

        for details in community_list:
            if details['type']:
                community = Community.objects.create(name=details['name'],
                                                     value=details['value'],
                                                     type=details['type'])
            else:
                community = Community.objects.create(name=details['name'],
                                                     value=details['value'])

            self.assertIsNotNone(community)
            self.assertEqual(details['name'], community.name)
            self.assertEqual(details['value'], community.value)
            self.assertEqual(details['type'] or COMMUNITY_TYPE_INGRESS,
                             community.type)
            self.assertEqual(details['str'], str(community))

    def test_get_type_html(self):
        expected = [
            '<span class="badge badge-info">'
            '<i class="fas fa-arrow-circle-up"></i> egress</span>',
            '<span class="badge badge-info">'
            '<i class="fas fa-arrow-circle-down"></i> ingress</span>',
            '<span class="badge badge-secondary">'
            '<i class="fas fa-ban"></i> unknown</span>',
        ]
        community_types = [
            COMMUNITY_TYPE_EGRESS,
            COMMUNITY_TYPE_INGRESS,
            'unknown',
        ]

        for i in range(len(community_types)):
            self.assertEqual(expected[i],
                             Community.objects.create(
                                 name='test{}'.format(i),
                                 value='64500:{}'.format(i),
                                 type=community_types[i]).get_type_html())


class CommunityViewsTestCase(ViewTestCase):
    def setUp(self):
        super(CommunityViewsTestCase, self).setUp()

        self.name = 'peering-all-exchanges'
        self.value = '64500:1'
        self.community = Community.objects.create(name=self.name,
                                                  value=self.value)

    def test_community_list_view(self):
        response = self.client.get(reverse('peering:community_list'))
        self.assertEqual(response.status_code, 200)

    def test_community_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:community_add'))
        self.assertEqual(response.status_code, 302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        response = self.client.get(reverse('peering:community_add'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create')

        # Try to create an object with valid data
        community_to_create = {
            'name': 'community-created',
            'value': '64500:1',
            'type': COMMUNITY_TYPE_INGRESS,
        }
        response = self.client.post(reverse('peering:community_add'),
                                    community_to_create)
        self.assertEqual(response.status_code, 302)
        self.does_object_exist(Community, community_to_create)

        # Try to create an object with invalid data
        community_not_to_create = {
            'name': 'community-not-created',
        }
        response = self.client.post(reverse('peering:community_add'),
                                    community_not_to_create)
        self.assertEqual(response.status_code, 200)
        self.does_object_not_exist(Community, community_not_to_create)

    def test_community_import_view(self):
        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:community_import'))
        self.assertEqual(response.status_code, 302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        response = self.client.get(reverse('peering:community_import'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Import')

        # Try to import an object with valid data
        community_to_import = {
            'csv': '''name,value,type,comment
                      community-created,64500:1,Ingress,''',
        }
        response = self.client.post(reverse('peering:community_import'),
                                    community_to_import)
        self.assertEqual(response.status_code, 302)
        self.does_object_exist(Community, {'pk': 1})

        # Try to create an object with invalid data
        community_not_to_import = {
            'csv': '''name,value,type,comment
                      community-not-created,64501:1,Ingress,''',
        }
        response = self.client.post(reverse('peering:community_import'),
                                    community_not_to_import)
        self.assertEqual(response.status_code, 302)
        self.does_object_exist(Community, {'pk': 2})

    def test_community_details_view(self):
        # No community PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('peering:community_details'))

        # Using a wrong PK, status should be 404 not found
        response = self.client.get(reverse('peering:community_details',
                                           kwargs={'pk': 666}))
        self.assertEqual(response.status_code, 404)

        # Using an existing PK, status should be 200 and the name of the
        # community should be somewhere in the HTML code
        response = self.client.get(self.community.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.name)

    def test_community_edit_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('peering:community_edit'))

        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:community_edit',
                                           kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        response = self.client.get(reverse('peering:community_edit',
                                           kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Update')

        # Still authenticated, wrong PK should be 404 not found
        response = self.client.get(reverse('peering:community_edit',
                                           kwargs={'pk': 2}))
        self.assertEqual(response.status_code, 404)

    def test_community_delete_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('peering:community_delete'))

        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:community_delete',
                                           kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        response = self.client.get(reverse('peering:community_delete',
                                           kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirm')

        # Still authenticated, wrong PK should be 404 not found
        response = self.client.get(reverse('peering:community_delete',
                                           kwargs={'pk': 2}))
        self.assertEqual(response.status_code, 404)

    def test_community_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:as_bulk_delete'))
        self.assertEqual(response.status_code, 302)


class InternetExchangeTestCase(TestCase):
    def test_import_peering_sessions(self):
        # Expected results
        expected = [
            # First case
            (1, 1, []),
            # Second case
            (0, 1, []),
            # Third case
            (0, 1, []),
            # Fourth case
            (0, 0, []),
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
        for i in range(len(expected)):
            ixp = InternetExchange.objects.create(name='Test {}'.format(i),
                                                  slug='test_{}'.format(i))
            self.assertEqual(expected[i],
                             ixp._import_peering_sessions(session_lists[i],
                                                          prefix_lists[i]))
            self.assertEqual(expected[i][1], len(ixp.get_peering_sessions()))

    def test_generate_configuration(self):
        expected = [
            {
                'ip_version': 6,
                'peers': {
                    1: {
                        'as_name': 'Test 1',
                        'max_prefixes': 0,
                        'sessions': [
                         {
                             'ip_address': '2001:db8::1',
                             'password': False,
                             'enabled': True, }
                        ]
                    },
                    2: {
                        'as_name': 'Test 2',
                        'max_prefixes': 0,
                        'sessions': [
                            {
                                'ip_address': '2001:db8::2',
                                'password': False,
                                'enabled': True,
                            }
                        ]
                    },
                    3: {
                        'as_name': 'Test 3',
                        'max_prefixes': 0,
                        'sessions': [
                            {
                                'ip_address': '2001:db8::3',
                                'password': False,
                                'enabled': True,
                            }
                        ]
                    },
                    4: {
                        'as_name': 'Test 4',
                        'max_prefixes': 0,
                        'sessions': [
                            {
                                'ip_address': '2001:db8::4',
                                'password': False,
                                'enabled': True,
                            }
                        ]
                    },
                    5: {
                        'as_name': 'Test 5',
                        'max_prefixes': 0,
                        'sessions': [
                            {
                                'ip_address': '2001:db8::5',
                                'password': False,
                                'enabled': True,
                            }
                        ]
                    },
                }
            },
            {'ip_version': 4, 'peers': {}},
        ]

        internet_exchange = InternetExchange.objects.create(name='Test',
                                                            slug='test')
        for i in range(1, 6):
            PeeringSession.objects.create(
                autonomous_system=AutonomousSystem.objects.create(
                    asn=i,
                    name='Test {}'.format(i)
                ),
                internet_exchange=internet_exchange,
                ip_address='2001:db8::{}'.format(i)
            )
        values = internet_exchange._generate_configuration_variables()
        self.assertEqual(values['peering_groups'], expected)


class PeeringSessionTestCase(TestCase):
    def test_does_exist(self):
        # No session, must expect None
        self.assertIsNone(PeeringSession.does_exist())

        # Prepare objects and create a peering session
        autonomous_system0 = AutonomousSystem.objects.create(asn=64500,
                                                             name='Test')
        internet_exchange0 = InternetExchange.objects.create(name='Test0',
                                                             slug='test0')
        peering_session0 = PeeringSession.objects.create(
            autonomous_system=autonomous_system0,
            internet_exchange=internet_exchange0,
            ip_address='2001:db8::1')

        # Make sure that the session has been created
        self.assertIsNotNone(peering_session0)
        # Make sure that the session is returned by calling does_exist()
        # without arguments (only one session in the database)
        self.assertIsNotNone(PeeringSession.does_exist())
        # Make sure we can retrieve the session with its IP
        self.assertEqual(peering_session0,
                         PeeringSession.does_exist(ip_address='2001:db8::1'))
        # Make sure we can retrieve the session with its IX
        self.assertEqual(peering_session0,
                         PeeringSession.does_exist(
                             internet_exchange=internet_exchange0))
        # Make sure we can retrieve the session with AS
        self.assertEqual(peering_session0,
                         PeeringSession.does_exist(
                             autonomous_system=autonomous_system0))

        # Create another peering session
        peering_session1 = PeeringSession.objects.create(
            autonomous_system=autonomous_system0,
            internet_exchange=internet_exchange0,
            ip_address='192.168.1.1')

        # Make sure that the session has been created
        self.assertIsNotNone(peering_session1)
        # More than one session, must expect None
        self.assertIsNone(PeeringSession.does_exist())
        # Make sure we can retrieve the session with its IP
        self.assertEqual(peering_session1,
                         PeeringSession.does_exist(ip_address='192.168.1.1'))
        # Make sure it returns None when using a field that the two sessions
        # have in common
        self.assertIsNone(PeeringSession.does_exist(
            internet_exchange=internet_exchange0))

        # Create a new IX
        internet_exchange1 = InternetExchange.objects.create(name='Test1',
                                                             slug='test1')

        # Make sure it returns None when there is no session
        self.assertIsNone(PeeringSession.does_exist(
            internet_exchange=internet_exchange1))

        # Create a new session with a already used IP in another OX
        peering_session2 = PeeringSession.objects.create(
            autonomous_system=autonomous_system0,
            internet_exchange=internet_exchange1,
            ip_address='2001:db8::1')

        # Make sure that the session has been created
        self.assertIsNotNone(peering_session2)
        # Make sure we have None, because two sessions will be found
        self.assertIsNone(PeeringSession.does_exist(ip_address='2001:db8::1'))
        # But if we narrow the search with the IX we must have the proper
        # session
        self.assertEqual(peering_session2, PeeringSession.does_exist(
            ip_address='2001:db8::1', internet_exchange=internet_exchange1))


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
                                       platform=PLATFORM_JUNOS)

        # Run test cases
        for i in range(len(expected)):
            self.assertEqual(expected[i],
                             len(router._napalm_bgp_neighbors_to_peer_list(
                                 napalm_dicts_list[i])))


class RouterViewsTestCase(ViewTestCase):
    def setUp(self):
        super(RouterViewsTestCase, self).setUp()

        self.name = 'test.router'
        self.hostname = 'test.router.example.org'
        self.router = Router.objects.create(name=self.name,
                                            hostname=self.hostname)

    def test_router_list_view(self):
        response = self.client.get(reverse('peering:router_list'))
        self.assertEqual(response.status_code, 200)

    def test_router_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:router_add'))
        self.assertEqual(response.status_code, 302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        response = self.client.get(reverse('peering:router_add'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create')

        # Try to create an object with valid data
        router_to_create = {
            'name': 'router.created',
            'hostname': 'router.created.example.com',
        }
        response = self.client.post(reverse('peering:router_add'),
                                    router_to_create)
        self.assertEqual(response.status_code, 302)
        self.does_object_exist(Router, router_to_create)

        # Try to create an object with invalid data
        router_not_to_create = {
            'name': 'router.notcreated',
        }
        response = self.client.post(reverse('peering:router_add'),
                                    router_not_to_create)
        self.assertEqual(response.status_code, 200)
        self.does_object_not_exist(Router, router_not_to_create)

    def test_router_import_view(self):
        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:router_import'))
        self.assertEqual(response.status_code, 302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        response = self.client.get(reverse('peering:router_import'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Import')

    def test_router_details_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('peering:router_details'))

        # Using a wrong PK, status should be 404 not found
        response = self.client.get(reverse('peering:router_details',
                                           kwargs={'pk': 2}))
        self.assertEqual(response.status_code, 404)

        # Using an existing PK, status should be 200 and the name of the AS
        # should be somewhere in the HTML code
        response = self.client.get(self.router.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.name)

    def test_router_edit_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('peering:router_edit'))

        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:router_edit',
                                           kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        response = self.client.get(reverse('peering:router_edit',
                                           kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Update')

        # Still authenticated, wrong PK should be 404 not found
        response = self.client.get(reverse('peering:router_edit',
                                           kwargs={'pk': 2}))
        self.assertEqual(response.status_code, 404)

    def test_router_delete_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('peering:router_delete'))

        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:router_delete',
                                           kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        response = self.client.get(reverse('peering:router_delete',
                                           kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirm')

        # Still authenticated, wrong AS should be 404 not found
        response = self.client.get(reverse('peering:router_delete',
                                           kwargs={'pk': 2}))
        self.assertEqual(response.status_code, 404)

    def test_router_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        response = self.client.get(reverse('peering:router_bulk_delete'))
        self.assertEqual(response.status_code, 302)
