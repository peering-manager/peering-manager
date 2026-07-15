import ipaddress

from django.core.exceptions import ValidationError
from django.test import TestCase

from net.models import Connection
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
    DuplicatePendingRequestError,
    LocationDiscoveryService,
    PrivateLocationProvider,
    PublicLocationProvider,
    PublicSessionResolver,
    SessionsAlreadyConfiguredError,
    build_location_discovery_service,
    build_peering_request_service,
)
from ..services.discovery import _format_ip_with_prefix, session_proposals_by_ixp


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
