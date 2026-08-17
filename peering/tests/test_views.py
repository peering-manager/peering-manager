import ipaddress

from django.test import TestCase

from bgp.models import Relationship
from net.models import Connection
from peeringdb.models import InternetExchange as PeeringDBIX
from peeringdb.models import IXLan, IXLanPrefix, Network, NetworkIXLan, Organization
from utils.testing import ViewTestCases

from ..enums import BGPSessionStatus, PeeringRequestStatus, PeeringRequestType
from ..models import *
from ..views.internet_exchange import InternetExchangePeeringDBImport


class AutonomousSystemTestCase(
    ViewTestCases.PrimaryObjectViewTestCase,
    ViewTestCases.GetObjectJournalViewTestCase,
):
    model = AutonomousSystem

    test_bulk_edit_objects = None

    @classmethod
    def setUpTestData(cls):
        AutonomousSystem.objects.bulk_create(
            [
                AutonomousSystem(asn=64501, name="Autonomous System 1"),
                AutonomousSystem(asn=64502, name="Autonomous System 2"),
                AutonomousSystem(asn=64503, name="Autonomous System 3"),
            ]
        )

        cls.form_data = {
            "asn": 64504,
            "name": "Autonomous System 4",
            "name_peeringdb_sync": False,
            "export_routing_policies": [],
            "import_routing_policies": [],
            "ipv4_max_prefixes": 0,
            "ipv4_max_prefixes_peeringdb_sync": False,
            "ipv6_max_prefixes": 0,
            "ipv6_max_prefixes_peeringdb_sync": False,
            "irr_as_set": None,
            "irr_as_set_peeringdb_sync": False,
            "comments": "",
            "affiliated": False,
            "tags": [],
        }


class BGPGroupTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = BGPGroup

    @classmethod
    def setUpTestData(cls):
        BGPGroup.objects.bulk_create(
            [
                BGPGroup(name="BGP Group 1", slug="bgp-group-1"),
                BGPGroup(name="BGP Group 2", slug="bgp-group-2"),
                BGPGroup(name="BGP Group 3", slug="bgp-group-3"),
            ]
        )

        cls.form_data = {
            "name": "BGP Group 4",
            "slug": "bgp-group-4",
            "communities": [],
            "export_routing_policies": [],
            "import_routing_policies": [],
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {"description": "New description"}


class DirectPeeringSessionTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = DirectPeeringSession

    @classmethod
    def setUpTestData(cls):
        local_as = AutonomousSystem.objects.create(asn=64501, name="Autonomous System 1", affiliated=True)
        a_s = AutonomousSystem.objects.create(asn=64502, name="Autonomous System 2")
        relationship_private_peering = Relationship.objects.create(name="Private Peering", slug="private-peering")
        DirectPeeringSession.objects.bulk_create(
            [
                DirectPeeringSession(
                    local_autonomous_system=local_as,
                    autonomous_system=a_s,
                    ip_address="192.0.2.1",
                    relationship=relationship_private_peering,
                ),
                DirectPeeringSession(
                    local_autonomous_system=local_as,
                    autonomous_system=a_s,
                    ip_address="192.0.2.2",
                    relationship=relationship_private_peering,
                ),
                DirectPeeringSession(
                    local_autonomous_system=local_as,
                    autonomous_system=a_s,
                    ip_address="192.0.2.3",
                    relationship=relationship_private_peering,
                ),
            ]
        )

        cls.form_data = {
            "local_autonomous_system": local_as.pk,
            "local_ip_address": None,
            "autonomous_system": a_s.pk,
            "ip_address": ipaddress.ip_interface("2001:db8::4/128"),
            "status": BGPSessionStatus.ENABLED,
            "multihop_ttl": 1,
            "relationship": relationship_private_peering.pk,
            "password": None,
            "encrypted_password": None,
            "bgp_group": None,
            "router": None,
            "export_routing_policies": [],
            "import_routing_policies": [],
            "bgp_state": None,
            "last_established_state": None,
            "accepted_prefix_count": 0,
            "advertised_prefix_count": 0,
            "received_prefix_count": 0,
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {
            "enabled": BGPSessionStatus.DISABLED,
            "comments": "New comments",
        }

    def test_local_autonomous_system_defaults_to_context_as(self):
        self.add_permissions("add")
        local_as = AutonomousSystem.objects.get(affiliated=True)
        self._set_context_as(local_as)

        response = self.client.get(self._get_url("add"))

        self.assertHttpStatus(response, 200)
        self.assertEqual(
            local_as.pk,
            response.context["form"].initial["local_autonomous_system"],
        )

    def test_context_as_default_is_overridden_by_query_string(self):
        self.add_permissions("add")
        local_as = AutonomousSystem.objects.get(affiliated=True)
        other = AutonomousSystem.objects.get(asn=64502)
        self._set_context_as(local_as)

        response = self.client.get(self._get_url("add"), data={"local_autonomous_system": other.pk})

        self.assertEqual(
            str(other.pk),
            response.context["form"].initial["local_autonomous_system"],
        )

    def _set_context_as(self, autonomous_system):
        self.user.preferences.refresh_from_db()
        self.user.preferences.set("context.as", autonomous_system.pk, commit=True)


class InternetExchangeTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = InternetExchange

    @classmethod
    def setUpTestData(cls):
        local_as = AutonomousSystem.objects.create(asn=64501, name="Autonomous System 1", affiliated=True)
        InternetExchange.objects.bulk_create(
            [
                InternetExchange(
                    name="Internet Exchange 1",
                    slug="ix-1",
                    local_autonomous_system=local_as,
                ),
                InternetExchange(
                    name="Internet Exchange 2",
                    slug="ix-2",
                    local_autonomous_system=local_as,
                ),
                InternetExchange(
                    name="Internet Exchange 3",
                    slug="ix-3",
                    local_autonomous_system=local_as,
                ),
            ]
        )

        cls.form_data = {
            "peeringdb_ixlan": None,
            "name": "Internet Exchange 4",
            "slug": "ix-4",
            "local_autonomous_system": local_as.pk,
            "communities": [],
            "export_routing_policies": [],
            "import_routing_policies": [],
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {"description": "New description"}


class InternetExchangePeeringDBImportTestCase(TestCase):
    """
    Tests the PeeringDB import of IXPs and connections, which must keep one IXP per affiliated AS.
    """

    @classmethod
    def setUpTestData(cls):
        cls.first_as = AutonomousSystem.objects.create(asn=64501, name="First AS", affiliated=True)
        cls.second_as = AutonomousSystem.objects.create(asn=64502, name="Second AS", affiliated=True)

        org = Organization.objects.create(id=1, name="Test Org")
        cls.pdb_ix = PeeringDBIX.objects.create(id=7, name="Test IX", org=org)
        cls.ixlan = IXLan.objects.create(id=7, ix=cls.pdb_ix)
        IXLanPrefix.objects.create(ixlan=cls.ixlan, prefix="192.0.2.0/24", protocol="IPv4")

        cls.netixlans = {}
        for i, autonomous_system in enumerate((cls.first_as, cls.second_as), start=1):
            network = Network.objects.create(
                id=i, org=org, asn=autonomous_system.asn, name=autonomous_system.name, name_long=autonomous_system.name
            )
            cls.netixlans[autonomous_system.asn] = NetworkIXLan.objects.create(
                asn=autonomous_system.asn,
                net=network,
                ixlan=cls.ixlan,
                ipaddr4=ipaddress.ip_interface(f"192.0.2.{i}/32"),
                speed=10000,
            )

    def _import_for(self, autonomous_system):
        return InternetExchangePeeringDBImport().import_ixps(
            autonomous_system, {self.ixlan: [self.netixlans[autonomous_system.asn]]}
        )

    def test_import_creates_ixp_and_connection(self):
        self.assertEqual((1, 1), self._import_for(self.first_as))

        ixp = InternetExchange.objects.get()
        self.assertEqual("Test IX", ixp.name)
        self.assertEqual("test-ix-7", ixp.slug)
        self.assertEqual(self.first_as, ixp.local_autonomous_system)
        self.assertEqual(self.ixlan, ixp.peeringdb_ixlan)

        connection = Connection.objects.get()
        self.assertEqual(ixp, connection.internet_exchange_point)
        self.assertEqual(self.netixlans[self.first_as.asn], connection.peeringdb_netixlan)

    def test_import_gives_each_affiliated_as_its_own_ixp(self):
        self._import_for(self.first_as)
        self.assertEqual((1, 1), self._import_for(self.second_as))

        first_ixp = InternetExchange.objects.get(local_autonomous_system=self.first_as)
        second_ixp = InternetExchange.objects.get(local_autonomous_system=self.second_as)
        self.assertNotEqual(first_ixp, second_ixp)
        self.assertEqual(("Test IX", "test-ix-7"), (first_ixp.name, first_ixp.slug))
        self.assertEqual(("Test IX (AS64502)", "test-ix-7-as64502"), (second_ixp.name, second_ixp.slug))

        # A connection must never end up under the IXP of another AS
        for autonomous_system, ixp in ((self.first_as, first_ixp), (self.second_as, second_ixp)):
            connection = Connection.objects.get(internet_exchange_point=ixp)
            self.assertEqual(self.netixlans[autonomous_system.asn], connection.peeringdb_netixlan)

    def test_import_reuses_own_ixp_whatever_its_slug(self):
        ixp = InternetExchange.objects.create(
            name="Renamed IX", slug="renamed-ix", local_autonomous_system=self.first_as, peeringdb_ixlan=self.ixlan
        )

        self.assertEqual((0, 1), self._import_for(self.first_as))
        self.assertEqual(ixp, InternetExchange.objects.get())
        self.assertEqual(ixp, Connection.objects.get().internet_exchange_point)

    def test_import_skips_netixlan_without_address(self):
        netixlan = NetworkIXLan.objects.create(
            asn=self.first_as.asn, net=self.netixlans[self.first_as.asn].net, ixlan=self.ixlan, speed=10000
        )

        self.assertEqual((1, 0), InternetExchangePeeringDBImport().import_ixps(self.first_as, {self.ixlan: [netixlan]}))
        self.assertFalse(Connection.objects.exists())


class InternetExchangePeeringSessionTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = InternetExchangePeeringSession

    @classmethod
    def setUpTestData(cls):
        local_as = AutonomousSystem.objects.create(asn=64501, name="Autonomous System 1", affiliated=True)
        cls.a_s = AutonomousSystem.objects.create(asn=64502, name="Autonomous System 2")
        cls.ixp = InternetExchange.objects.create(
            name="Internet Exchange 1", slug="ix-1", local_autonomous_system=local_as
        )
        cls.ixp_connection = Connection.objects.create(vlan=2000, internet_exchange_point=cls.ixp)
        InternetExchangePeeringSession.objects.bulk_create(
            [
                InternetExchangePeeringSession(
                    autonomous_system=cls.a_s,
                    ixp_connection=cls.ixp_connection,
                    ip_address="192.0.2.1",
                ),
                InternetExchangePeeringSession(
                    autonomous_system=cls.a_s,
                    ixp_connection=cls.ixp_connection,
                    ip_address="192.0.2.2",
                ),
                InternetExchangePeeringSession(
                    autonomous_system=cls.a_s,
                    ixp_connection=cls.ixp_connection,
                    ip_address="192.0.2.3",
                ),
            ]
        )

        cls.form_data = {
            "autonomous_system": cls.a_s.pk,
            "internet_exchange": cls.ixp.pk,
            "ixp_connection": cls.ixp_connection.pk,
            "ip_address": ipaddress.ip_address("2001:db8::4"),
            "multihop_ttl": 1,
            "password": None,
            "encrypted_password": None,
            "is_route_server": False,
            "enabled": True,
            "export_routing_policies": [],
            "import_routing_policies": [],
            "bgp_state": None,
            "last_established_state": None,
            "accepted_prefix_count": 0,
            "advertised_prefix_count": 0,
            "received_prefix_count": 0,
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {
            "is_route_server": True,
            "enabled": False,
            "comments": "New comments",
        }


class PeeringRequestTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = PeeringRequest

    test_bulk_edit_objects = None

    @classmethod
    def setUpTestData(cls):
        local_as = AutonomousSystem.objects.create(asn=64501, name="Autonomous System 1", affiliated=True)
        PeeringRequest.objects.bulk_create(
            [
                PeeringRequest(
                    requesting_asn=64601,
                    local_autonomous_system=local_as,
                    request_type=PeeringRequestType.PUBLIC_PEERING,
                    status=PeeringRequestStatus.PENDING,
                ),
                PeeringRequest(
                    requesting_asn=64602,
                    local_autonomous_system=local_as,
                    request_type=PeeringRequestType.PUBLIC_PEERING,
                    status=PeeringRequestStatus.PENDING,
                ),
                PeeringRequest(
                    requesting_asn=64603,
                    local_autonomous_system=local_as,
                    request_type=PeeringRequestType.PRIVATE_PEERING,
                    status=PeeringRequestStatus.PENDING,
                ),
            ]
        )

        cls.form_data = {
            "requesting_asn": 64604,
            "local_autonomous_system": local_as.pk,
            "request_type": PeeringRequestType.PUBLIC_PEERING,
            "status": PeeringRequestStatus.PENDING,
            "decision_comment": "",
            "comments": "",
            "tags": [],
        }
