import ipaddress
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from net.models import Connection, PrefixListEntry
from peeringdb.models import (
    Facility,
    IXLan,
    IXLanPrefix,
    Network,
    NetworkFacility,
    NetworkIXLan,
    Organization,
)
from peeringdb.models import InternetExchange as PeeringDBIX

from ..enums import PeeringRequestStatus, PeeringRequestType
from ..models import (
    AutonomousSystem,
    InternetExchange,
    InternetExchangePeeringSession,
    PeeringRequest,
)
from ..services import (
    BgpqPrefixSource,
    DuplicatePendingRequestError,
    LocationDiscoveryService,
    PrefixListEntryRepository,
    PrefixSpec,
    PrefixSynchroniser,
    PrivateLocationProvider,
    PublicLocationProvider,
    PublicSessionResolver,
    SessionsAlreadyConfiguredError,
    build_location_discovery_service,
    build_peering_request_service,
    build_prefix_synchroniser,
    normalise_prefix_list_entries,
)
from ..services.discovery import _format_ip_with_prefix, session_proposals_by_ixp
from .mocked_data import mocked_subprocess_popen


class PeeringServicesTestMixin:
    @classmethod
    def setUpTestData(cls):
        # High 32-bit ASNs unlikely to be allocated to real networks
        cls.org = Organization.objects.create(id=1, name="Test Org")
        cls.affiliated_as = AutonomousSystem.objects.create(asn=4199999990, name="Affiliated AS", affiliated=True)
        cls.peer_network = Network.objects.create(
            id=1, org=cls.org, asn=4199999991, name="Requester Network", name_long="Requester Network Inc"
        )
        cls.affiliated_network = Network.objects.create(
            id=2, org=cls.org, asn=4199999990, name="Affiliated AS", name_long="Affiliated AS Corp"
        )
        cls.pdb_ix = PeeringDBIX.objects.create(id=1, name="Test IX", org=cls.org)
        cls.ixlan = IXLan.objects.create(id=42, ix=cls.pdb_ix, name="Test IX LAN")
        IXLanPrefix.objects.create(ixlan=cls.ixlan, prefix="192.0.2.0/24", protocol="IPv4")
        IXLanPrefix.objects.create(ixlan=cls.ixlan, prefix="2001:db8::/64", protocol="IPv6")
        cls.ix = InternetExchange.objects.create(
            name="Test IX", slug="test-ix", local_autonomous_system=cls.affiliated_as, peeringdb_ixlan=cls.ixlan
        )
        cls.connection = Connection.objects.create(
            internet_exchange_point=cls.ix, ipv4_address="192.0.2.254/24", ipv6_address="2001:db8::ffff/64"
        )
        NetworkIXLan.objects.create(
            asn=4199999991,
            net=cls.peer_network,
            ixlan=cls.ixlan,
            ipaddr4="192.0.2.1",
            ipaddr6="2001:db8::1",
            speed=10000,
        )
        NetworkIXLan.objects.create(
            asn=4199999990,
            net=cls.affiliated_network,
            ixlan=cls.ixlan,
            ipaddr4="192.0.2.254",
            ipaddr6="2001:db8::ffff",
            speed=10000,
        )
        cls.facility = Facility.objects.create(id=17, name="Test Facility", org=cls.org)
        # Both networks present at the facility so it is a shared private location
        NetworkFacility.objects.create(net=cls.peer_network, fac=cls.facility, local_asn=4199999991)
        NetworkFacility.objects.create(net=cls.affiliated_network, fac=cls.facility, local_asn=4199999990)


class PeeringRequestServiceTest(PeeringServicesTestMixin, TestCase):
    def _submit(self, **overrides):
        kwargs = {
            "local_autonomous_system": self.affiliated_as,
            "requesting_asn": 4199999991,
            "request_type": PeeringRequestType.PUBLIC_PEERING,
            "sessions": [{"local_ip": "192.0.2.1/24", "location": "pdb:ix:42", "peer_ip": "192.0.2.254"}],
        }
        kwargs.update(overrides)
        return build_peering_request_service().submit(**kwargs)

    def test_submit_public(self):
        pr = self._submit()
        self.assertEqual(pr.status, PeeringRequestStatus.PENDING)
        session = pr.requested_sessions.get()
        self.assertEqual(session.ixp_connection, self.connection)
        self.assertIsNone(session.peeringdb_facility)

    def test_submit_private(self):
        pr = self._submit(
            request_type=PeeringRequestType.PRIVATE_PEERING,
            sessions=[{"local_ip": "192.0.2.1/30", "location": "pdb:fac:17", "peer_ip": "192.0.2.2/30"}],
        )
        session = pr.requested_sessions.get()
        self.assertEqual(session.peeringdb_facility, self.facility)
        self.assertEqual(str(session.peer_ip_address), "192.0.2.2/30")

    def test_submit_private_rejects_bare_facility_id(self):
        with self.assertRaises(ValidationError):
            self._submit(
                request_type=PeeringRequestType.PRIVATE_PEERING,
                sessions=[{"local_ip": "192.0.2.1/30", "location": "17", "peer_ip": "192.0.2.2/30"}],
            )
        self.assertFalse(PeeringRequest.objects.exists())

    def test_submit_unsupported_type_raises(self):
        with self.assertRaises(ValidationError):
            self._submit(request_type="carrier")
        self.assertFalse(PeeringRequest.objects.exists())

    def test_submit_duplicate_pending_raises(self):
        self._submit()
        with self.assertRaises(DuplicatePendingRequestError) as ctx:
            self._submit()
        self.assertIn("192.0.2.1", ctx.exception.ips)
        self.assertEqual(PeeringRequest.objects.count(), 1)

    def test_submit_existing_session_raises(self):
        requester = AutonomousSystem.objects.create(asn=4199999991, name="Requester")
        InternetExchangePeeringSession.objects.create(
            autonomous_system=requester, ixp_connection=self.connection, ip_address="192.0.2.1"
        )
        with self.assertRaises(SessionsAlreadyConfiguredError):
            self._submit()
        self.assertFalse(PeeringRequest.objects.exists())


class SessionResolverTest(PeeringServicesTestMixin, TestCase):
    def test_supports_predicates(self):
        resolver = PublicSessionResolver()
        self.assertTrue(resolver.supports(PeeringRequestType.PUBLIC_PEERING))
        self.assertFalse(resolver.supports(PeeringRequestType.PRIVATE_PEERING))

    def test_public_resolve_matches_connection_on_host(self):
        resolved = PublicSessionResolver().resolve(
            {"local_ip": "192.0.2.1/24", "location": "pdb:ix:42", "peer_ip": "192.0.2.254"}
        )
        self.assertEqual(resolved.connection, self.connection)
        self.assertIsNone(resolved.facility)

    def test_public_resolve_unknown_peer_ip_raises(self):
        with self.assertRaises(ValidationError):
            PublicSessionResolver().resolve(
                {"local_ip": "192.0.2.1/24", "location": "pdb:ix:42", "peer_ip": "192.0.2.9"}
            )


class LocationDiscoveryServiceTest(PeeringServicesTestMixin, TestCase):
    def _discover(self, location_type=None):
        return build_location_discovery_service().discover(
            affiliated=self.affiliated_as, network=self.peer_network, location_type=location_type
        )

    def test_public_only(self):
        locations = self._discover(location_type=PeeringRequestType.PUBLIC_PEERING)
        self.assertTrue(locations)
        self.assertTrue(all(loc["peering_type"] == PeeringRequestType.PUBLIC_PEERING for loc in locations))
        self.assertEqual(locations[0]["location"], "pdb:ix:42")

    def test_private_only(self):
        locations = self._discover(location_type=PeeringRequestType.PRIVATE_PEERING)
        self.assertTrue(locations)
        self.assertTrue(all(loc["peering_type"] == PeeringRequestType.PRIVATE_PEERING for loc in locations))
        self.assertEqual(locations[0]["location"], "pdb:fac:17")

    def test_both_when_unfiltered(self):
        peering_types = {loc["peering_type"] for loc in self._discover()}
        self.assertEqual(peering_types, {PeeringRequestType.PUBLIC_PEERING, PeeringRequestType.PRIVATE_PEERING})

    def test_supports_predicates(self):
        self.assertTrue(PublicLocationProvider().supports(None))
        self.assertFalse(PublicLocationProvider().supports(PeeringRequestType.PRIVATE_PEERING))
        self.assertTrue(PrivateLocationProvider().supports(None))
        self.assertFalse(PrivateLocationProvider().supports(PeeringRequestType.PUBLIC_PEERING))

    def test_empty_when_no_provider_supports(self):
        service = LocationDiscoveryService(providers=[])
        self.assertEqual(service.discover(affiliated=self.affiliated_as, network=self.peer_network), [])


class SessionProposalsTest(PeeringServicesTestMixin, TestCase):
    def _proposals(self):
        return session_proposals_by_ixp([self.ix], self.peer_network)[self.ix.pk]

    def test_proposal_content_both_address_families(self):
        by_af = {p["address_family"]: p for p in self._proposals()}
        self.assertEqual(set(by_af), {4, 6})

        self.assertEqual(by_af[4]["local_ip"], "192.0.2.1/24")
        self.assertEqual(str(ipaddress.ip_interface(by_af[4]["peer_ip"]).ip), "192.0.2.254")
        self.assertFalse(by_af[4]["existing"])

        self.assertEqual(by_af[6]["local_ip"], "2001:db8::1/64")
        self.assertEqual(str(ipaddress.ip_interface(by_af[6]["peer_ip"]).ip), "2001:db8::ffff")
        self.assertFalse(by_af[6]["existing"])

    def test_existing_flag_set_when_session_present(self):
        requester = AutonomousSystem.objects.create(asn=4199999991, name="Requester")
        InternetExchangePeeringSession.objects.create(
            autonomous_system=requester, ixp_connection=self.connection, ip_address="192.0.2.1"
        )
        by_af = {p["address_family"]: p for p in self._proposals()}
        self.assertTrue(by_af[4]["existing"])
        self.assertFalse(by_af[6]["existing"])

    def test_format_ip_with_prefix(self):
        networks = [ipaddress.ip_network("192.0.2.0/24")]
        self.assertEqual(_format_ip_with_prefix("192.0.2.1", networks), "192.0.2.1/24")
        # No matching network falls back to the bare host
        self.assertEqual(_format_ip_with_prefix("192.0.2.1", []), "192.0.2.1")


class _RecordingPrefixSource:
    """Test double returning a canned prefix dict without touching bgpq/subprocess."""

    def __init__(self, prefixes):
        self._prefixes = prefixes
        self.calls = 0

    def retrieve(self, autonomous_system):
        self.calls += 1
        return self._prefixes


class NormalisePrefixListEntriesTest(TestCase):
    def test_normalise(self):
        self.assertEqual(set(), normalise_prefix_list_entries(None))
        self.assertEqual(set(), normalise_prefix_list_entries({"ipv6": [], "ipv4": []}))

        entries = normalise_prefix_list_entries(
            {
                "ipv6": [
                    {"prefix": "2001:DB8::/32", "exact": False, "greater-equal": 33, "less-equal": 48},
                    {"prefix": "2001:0db8:0000::/32", "exact": False, "greater-equal": 33, "less-equal": 48},
                ],
                "ipv4": [{"prefix": "192.0.2.0/24", "exact": True}, {"prefix": "198.51.100.0/24"}],
            }
        )
        self.assertEqual(
            {
                PrefixSpec("2001:db8::/32", False, 33, 48),
                PrefixSpec("192.0.2.0/24", True),
                PrefixSpec("198.51.100.0/24", False),
            },
            entries,
        )


class BgpqPrefixSourceTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.autonomous_system = AutonomousSystem.objects.create(asn=65537, name="Test", irr_as_set="AS-MOCKED")

    def test_retrieve(self):
        with patch("peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen):
            prefixes = BgpqPrefixSource().retrieve(self.autonomous_system)
        self.assertEqual(1, len(prefixes["ipv6"]))
        self.assertEqual(1, len(prefixes["ipv4"]))

    def test_retrieve_disabled_returns_empty(self):
        self.autonomous_system.retrieve_prefixes = False
        self.assertEqual({"ipv6": [], "ipv4": []}, BgpqPrefixSource().retrieve(self.autonomous_system))

    def test_retrieve_unresolvable_returns_empty(self):
        self.autonomous_system.irr_as_set = "AS-ERROR"
        with patch("peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen):
            self.assertEqual({"ipv6": [], "ipv4": []}, BgpqPrefixSource().retrieve(self.autonomous_system))


class PrefixSynchroniserTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a1 = AutonomousSystem.objects.create(asn=65538, name="AS1")
        cls.a2 = AutonomousSystem.objects.create(asn=65539, name="AS2")

    def test_synchronise_dedups_relinks_and_reclaims(self):
        synchroniser = build_prefix_synchroniser()
        synchroniser.synchronise(
            self.a1,
            {
                "ipv6": [{"prefix": "2001:db8::/32", "exact": False, "greater-equal": 33, "less-equal": 48}],
                "ipv4": [{"prefix": "192.0.2.0/24", "exact": True}, {"prefix": "198.51.100.0/24", "exact": True}],
            },
        )
        self.assertEqual(3, PrefixListEntry.objects.count())

        # A prefix shared with another AS is stored once and linked, not duplicated
        synchroniser.synchronise(self.a2, {"ipv6": [], "ipv4": [{"prefix": "192.0.2.0/24", "exact": True}]})
        self.assertEqual(3, PrefixListEntry.objects.count())
        self.assertEqual(2, PrefixListEntry.objects.get(prefix="192.0.2.0/24", exact=True).autonomous_systems.count())

        # Re-syncing drops stale links but keeps rows still shared with other autonomous systems
        synchroniser.synchronise(self.a1, {"ipv6": [], "ipv4": [{"prefix": "198.51.100.0/24", "exact": True}]})
        self.assertEqual(["198.51.100.0/24"], [str(e.prefix) for e in self.a1.prefix_list_entries.all()])
        self.assertEqual(3, PrefixListEntry.objects.count())

        # The now-unreferenced entry is reclaimed
        self.assertEqual(1, PrefixListEntryRepository().delete_orphans())
        self.assertEqual(2, PrefixListEntry.objects.count())

    def test_get_reads_through_once(self):
        source = _RecordingPrefixSource({"ipv6": [{"prefix": "2001:db8::/32", "exact": True}], "ipv4": []})
        synchroniser = PrefixSynchroniser(source=source, repository=PrefixListEntryRepository())

        self.assertEqual([{"prefix": "2001:db8::/32", "exact": True}], synchroniser.get(self.a1, address_family=6))
        self.assertIsNotNone(self.a1.prefixes_updated)

        # The stored value is reused, the source is not hit again
        synchroniser.get(self.a1)
        self.assertEqual(1, source.calls)

        # An AS-SET resolving to nothing is still marked as fetched, so it does not refetch on every access
        empty_source = _RecordingPrefixSource({"ipv6": [], "ipv4": []})
        synchroniser = PrefixSynchroniser(source=empty_source, repository=PrefixListEntryRepository())
        self.assertEqual({"ipv6": [], "ipv4": []}, synchroniser.get(self.a2))
        self.assertIsNotNone(self.a2.prefixes_updated)
        synchroniser.get(self.a2)
        self.assertEqual(1, empty_source.calls)
