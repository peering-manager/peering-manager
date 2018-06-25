from __future__ import unicode_literals

import ipaddress

from django.test import TestCase
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

        self.model = AutonomousSystem
        self.asn = 29467
        self.as_name = 'LuxNetwork S.A.'
        self.autonomous_system = AutonomousSystem.objects.create(
            asn=self.asn, name=self.as_name)

    def test_as_list_view(self):
        self.get_request('peering:as_list')

    def test_as_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:as_add', expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:as_add', contains='Create')

        # Try to create an object with valid data
        as_to_create = {
            'asn': 64500,
            'name': 'as-created',
        }
        self.post_request('peering:as_add', data=as_to_create)
        self.does_object_exist(as_to_create)

        # Try to create an object with invalid data
        as_not_to_create = {
            'asn': 64501,
        }
        self.post_request('peering:as_add', data=as_not_to_create)
        self.does_object_not_exist(as_not_to_create)

    def test_as_import_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:as_import', expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:as_import', contains='Import')

        # Try to import an object with valid data
        as_to_import = {
            'csv': '''asn,name,irr_as_set,ipv6_max_prefixes,ipv4_max_prefixes,comment
                      64500,as-created,,,,''',
        }
        self.post_request('peering:as_import', data=as_to_import)
        self.does_object_exist({'asn': 64500})

        # Try to create an object with invalid data
        as_not_to_import = {
            'csv': '''asn,name,irr_as_set,ipv6_max_prefixes,ipv4_max_prefixes,comment
                      64501,,,,,''',
        }
        self.post_request('peering:as_import', data=as_not_to_import)
        self.does_object_not_exist({'asn': 64501})

    def test_as_import_from_peeringdb_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:as_import_from_peeringdb',
                         expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:as_import_from_peeringdb',
                         contains='PeeringDB')

        # Using a wrong AS number
        self.post_request('peering:as_import_from_peeringdb',
                          data={'asn': 64500})
        self.does_object_not_exist({'asn': 64500})

        # Using an existing AS, status should be OK
        self.post_request('peering:as_import_from_peeringdb',
                          data={'asn': self.asn})
        self.does_object_exist({'asn': self.asn})

    def test_as_details_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:as_details')

        # Using a wrong AS number, status should be 404 not found
        self.get_request('peering:as_details', params={'asn': 64500},
                         expected_status_code=404)

        # Using an existing AS, status should be 200 and the name of the AS
        # should be somewhere in the HTML code
        self.get_request('peering:as_details', params={'asn': self.asn},
                         contains='LuxNetwork')

    def test_as_edit_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:as_edit')

        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:as_edit', params={'asn': self.asn},
                         expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:as_edit', params={'asn': self.asn},
                         contains='Update')

        # Still authenticated, wrong AS should be 404 not found
        self.get_request('peering:as_edit', params={'asn': 64500},
                         expected_status_code=404)

    def test_as_delete_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:as_delete')

        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:as_delete', params={'asn': self.asn},
                         expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:as_delete', params={'asn': self.asn},
                         contains='Confirm')

        # Still authenticated, wrong AS should be 404 not found
        self.get_request('peering:as_delete', params={'asn': 64500},
                         expected_status_code=404)

    def test_as_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:as_bulk_delete', expected_status_code=302)

    def test_as_peeringdb_sync_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:as_peeringdb_sync')

        # Using a wrong AS number, status should be 404 not found
        self.get_request('peering:as_peeringdb_sync', params={'asn': 64500},
                         expected_status_code=404)

        # Using an existing AS, status should be OK
        self.get_request('peering:as_peeringdb_sync', params={'asn': self.asn},
                         expected_status_code=302)

    def test_as_peering_sessions_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:as_peering_sessions')

        # Using a wrong AS number, status should be 404 not found
        self.get_request('peering:as_peering_sessions', params={'asn': 64500},
                         expected_status_code=404)

        # Using an existing AS, status should be OK
        self.get_request('peering:as_peering_sessions',
                         params={'asn': self.asn})


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

        self.model = Community
        self.name = 'peering-all-exchanges'
        self.value = '64500:1'
        self.community = Community.objects.create(name=self.name,
                                                  value=self.value)

    def test_community_list_view(self):
        self.get_request('peering:community_list')

    def test_community_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:community_add', expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:community_add', contains='Create')

        # Try to create an object with valid data
        community_to_create = {
            'name': 'community-created',
            'value': '64500:1',
            'type': COMMUNITY_TYPE_INGRESS,
        }
        self.post_request('peering:community_add', data=community_to_create)
        self.does_object_exist(community_to_create)

        # Try to create an object with invalid data
        community_not_to_create = {
            'name': 'community-not-created',
        }
        self.post_request('peering:community_add',
                          data=community_not_to_create)
        self.does_object_not_exist(community_not_to_create)

    def test_community_import_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:community_import', expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:community_import', contains='Import')

        # Try to import an object with valid data
        community_to_import = {
            'csv': '''name,value,type,comment
                      community-created,64500:1,Ingress,''',
        }
        self.post_request('peering:community_import', data=community_to_import)
        self.does_object_exist({'pk': 2})

        # Try to create an object with invalid data
        community_not_to_import = {
            'csv': '''name,value,type,comment
                      community-not-created,,Ingress,''',
        }
        self.post_request('peering:community_import',
                          data=community_not_to_import)
        self.does_object_not_exist({'pk': 3})

    def test_community_details_view(self):
        # No community PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:community_details')

        # Using a wrong PK, status should be 404 not found
        self.get_request('peering:community_details', params={'pk': 666},
                         expected_status_code=404)

        # Using an existing PK, status should be 200 and the name of the
        # community should be somewhere in the HTML code
        self.get_request('peering:community_details', params={'pk': 1},
                         contains=self.name)

    def test_community_edit_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:community_edit')

        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:community_edit', params={'pk': 1},
                         expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:community_edit', params={'pk': 1},
                         contains='Update')

        # Still authenticated, wrong PK should be 404 not found
        self.get_request('peering:community_edit', params={'pk': 2},
                         expected_status_code=404)

    def test_community_delete_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:community_delete')

        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:community_delete', params={'pk': 1},
                         expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:community_delete', params={'pk': 1},
                         contains='Confirm')

        # Still authenticated, wrong PK should be 404 not found
        self.get_request('peering:community_delete', params={'pk': 2},
                         expected_status_code=404)

    def test_community_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:as_bulk_delete', expected_status_code=302)


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


class InternetExchangeViewsTestCase(ViewTestCase):
    def setUp(self):
        super(InternetExchangeViewsTestCase, self).setUp()

        self.model = InternetExchange
        self.name = 'Test IX'
        self.slug = 'test-ix'
        self.ix = InternetExchange.objects.create(name=self.name,
                                                  slug=self.slug)
        self.asn = AutonomousSystem.objects.create(asn=64500, name='Test')
        self.session = PeeringSession.objects.create(
            internet_exchange=self.ix, autonomous_system=self.asn,
            ip_address='2001:db8::1')
        self.community = Community.objects.create(name='Test', value='64500:1')

    def test_ix_list_view(self):
        self.get_request('peering:ix_list')

    def test_ix_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:ix_add', expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:ix_add', contains='Create')

        # Try to create an object with valid data
        ix_to_create = {
            'name': 'ix-created',
            'slug': 'ix-created',
        }
        self.post_request('peering:ix_add', data=ix_to_create)
        self.does_object_exist(ix_to_create)

        # Try to create an object with invalid data
        ix_not_to_create = {
            'name': 'ix-notcreated',
        }
        self.post_request('peering:ix_add', data=ix_not_to_create)
        self.does_object_not_exist(ix_not_to_create)

    def test_ix_import_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:ix_import', expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:ix_import', contains='Import')

        # Try to import an object with valid data
        ix_to_import = {
            'csv': '''name,slug,ipv6_address,ipv4_address,configuration_template,router,check_bgp_session_states,comment
                      ix-created,ix-created,,,,,,''',
        }
        self.post_request('peering:ix_import', data=ix_to_import)
        self.does_object_exist({'slug': 'ix-created'})

        # Try to create an object with invalid data
        ix_to_import = {
            'csv': '''name,slug,ipv6_address,ipv4_address,configuration_template,router,check_bgp_session_states,comment
                      ix-not-created,,,,,,,''',
        }
        self.post_request('peering:ix_import', data=ix_to_import)
        self.does_object_not_exist({'slug': 'ix-not-reated'})

    def test_ix_peeringdb_import_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:ix_peeringdb_import',
                         expected_status_code=302)

    def test_ix_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:ix_bulk_delete', expected_status_code=302)

    def test_ix_details_view(self):
        # No slug given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:ix_details')

        # Using a wrong slug, status should be 404 not found
        self.get_request('peering:ix_details', params={'slug': 'not-found'},
                         expected_status_code=404)

        # Using an existing slug, status should be 200 and the name of the IX
        # should be somewhere in the HTML code
        self.get_request('peering:ix_details', params={'slug': self.slug},
                         contains=self.name)

    def test_ix_edit_view(self):
        # No slug given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:ix_edit')

        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:ix_edit', params={'slug': self.slug},
                         expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:ix_edit', params={'slug': self.slug},
                         contains='Update')

        # Still authenticated, wrong slug should be 404 not found
        self.get_request('peering:ix_edit', params={'slug': 'not-found'},
                         expected_status_code=404)

    def test_ix_delete_view(self):
        # No slug given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:ix_delete')

        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:ix_delete', params={'slug': self.slug},
                         expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:ix_delete', params={'slug': self.slug},
                         contains='Confirm')

        # Still authenticated, wrong slug should be 404 not found
        self.get_request('peering:ix_delete', params={'slug': 'not-found'},
                         expected_status_code=404)

    def test_ix_update_communities_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:ix_update_communities',
                         params={'slug': self.slug}, expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:ix_update_communities',
                         params={'slug': self.slug})

        # IX not found
        self.get_request('peering:ix_update_communities',
                         params={'slug': 'not-found'},
                         expected_status_code=404)

        # Check if adding a community works
        self.assertFalse(self.ix.communities.all())
        self.post_request('peering:ix_update_communities',
                          params={'slug': self.slug},
                          data={'communities': self.community.pk})
        self.assertTrue(self.ix.communities.all())

    def test_ix_peering_sessions_view(self):
        # Not logged in, 200 OK but not contains Add Peering Session button
        self.get_request('peering:ix_peering_sessions',
                         params={'slug': self.slug},
                         notcontains='Add a Peering Session')

        # Authenticate and retry, 200 OK and should contains Add Peering
        # Session button
        self.authenticate_user()
        self.get_request('peering:ix_peering_sessions',
                         params={'slug': self.slug},
                         contains='Add a Peering Session')

        # IX not found
        self.get_request('peering:ix_peering_sessions',
                         params={'slug': 'not-found'},
                         expected_status_code=404)


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


class PeeringSessionViewsTestCase(ViewTestCase):
    def setUp(self):
        super(PeeringSessionViewsTestCase, self).setUp()

        self.model = PeeringSession
        self.ip_address = '2001:db8::64:501'
        self.as64500 = AutonomousSystem.objects.create(asn=64500, name='Test')
        self.ix = InternetExchange.objects.create(name='Test', slug='test')
        self.peering_session = PeeringSession.objects.create(
            autonomous_system=self.as64500, internet_exchange=self.ix,
            ip_address=self.ip_address)

    def test_peering_session_list_view(self):
        self.get_request('peering:peering_session_list')

    def test_peering_session_details_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:peering_session_details')

        # Using a wrong PK, status should be 404 not found
        self.get_request('peering:peering_session_details', params={'pk': 2},
                         expected_status_code=404)

        # Using an existing PK, status should be 200 and the name of the IP
        # should be somewhere in the HTML code
        self.get_request('peering:peering_session_details', params={'pk': 1},
                         contains=self.ip_address)

    def test_peering_session_edit_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:peering_session_edit')

        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:peering_session_edit', params={'pk': 1},
                         expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:peering_session_edit', params={'pk': 1},
                         contains='Update')

        # Still authenticated, wrong PK should be 404 not found
        self.get_request('peering:peering_session_edit', params={'pk': 2},
                         expected_status_code=404)

    def test_peering_session_delete_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:peering_session_delete')

        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:peering_session_delete', params={'pk': 1},
                         expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:peering_session_delete', params={'pk': 1},
                         contains='Confirm')

        # Still authenticated, wrong router should be 404 not found
        self.get_request('peering:peering_session_delete', params={'pk': 2},
                         expected_status_code=404)

    def test_router_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:peering_session_bulk_delete',
                         expected_status_code=302)


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

        self.model = Router
        self.name = 'test.router'
        self.hostname = 'test.router.example.org'
        self.router = Router.objects.create(name=self.name,
                                            hostname=self.hostname)

    def test_router_list_view(self):
        self.get_request('peering:router_list')

    def test_router_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:router_add', expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:router_add', contains='Create')

        # Try to create an object with valid data
        router_to_create = {
            'name': 'router.created',
            'hostname': 'router.created.example.com',
        }
        self.post_request('peering:router_add', data=router_to_create)
        self.does_object_exist(router_to_create)

        # Try to create an object with invalid data
        router_not_to_create = {
            'name': 'router.notcreated',
        }
        self.post_request('peering:router_add', data=router_not_to_create)
        self.does_object_not_exist(router_not_to_create)

    def test_router_import_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:router_import', expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:router_import', contains='Import')

        # Try to import an object with valid data
        router_to_import = {
            'csv': '''name,hostname,platform,comment
                      router-created,rt-created.example.com,Other,''',
        }
        self.post_request('peering:router_import', data=router_to_import)
        self.does_object_exist({'pk': 2})

        # Try to create an object with invalid data
        router_not_to_import = {
            'csv': '''name,hostname,platform,comment
                      router-not-created,,Other,''',
        }
        self.post_request('peering:router_import', data=router_not_to_import)
        self.does_object_not_exist({'pk': 3})

    def test_router_details_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:router_details')

        # Using a wrong PK, status should be 404 not found
        self.get_request('peering:router_details', params={'pk': 2},
                         expected_status_code=404)

        # Using an existing PK, status should be 200 and the name of the router
        # should be somewhere in the HTML code
        self.get_request('peering:router_details', params={'pk': 1},
                         contains=self.name)

    def test_router_edit_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:router_edit')

        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:router_edit', params={'pk': 1},
                         expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:router_edit', params={'pk': 1},
                         contains='Update')

        # Still authenticated, wrong PK should be 404 not found
        self.get_request('peering:router_edit', params={'pk': 2},
                         expected_status_code=404)

    def test_router_delete_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request('peering:router_delete')

        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:router_delete', params={'pk': 1},
                         expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request('peering:router_delete', params={'pk': 1},
                         contains='Confirm')

        # Still authenticated, wrong router should be 404 not found
        self.get_request('peering:router_delete', params={'pk': 2},
                         expected_status_code=404)

    def test_router_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request('peering:router_bulk_delete',
                         expected_status_code=302)
