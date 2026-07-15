from django.contrib.auth.models import Permission, User
from django.db import connection as db_connection
from django.test import SimpleTestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from drf_spectacular.generators import SchemaGenerator
from rest_framework import status

from bgp.models import Relationship
from net.models import Connection
from peeringdb.models import (
    Facility,
    IXLan,
    Network,
    NetworkContact,
    NetworkIXLan,
    Organization,
)
from peeringdb.models import InternetExchange as PeeringDBIX
from users.models import Token
from utils.testing import APITestCase

from ..enums import PeeringRequestStatus, PeeringRequestType
from ..models import (
    AutonomousSystem,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    PeeringRequest,
    RequestedSession,
)


class PortalAPITestMixin:
    @classmethod
    def setUpTestData(cls):
        # This test relies on the fact that ASNs must be public, so we use high 32-bit
        # ASNs unlikely to be allocated to actual networks today
        cls.org = Organization.objects.create(id=1, name="Test Org")
        cls.affiliated_as = AutonomousSystem.objects.create(asn=4199999990, name="Affiliated AS", affiliated=True)
        cls.peeringdb_network = Network.objects.create(
            id=1,
            org=cls.org,
            asn=4199999991,
            name="Requester Network",
            name_long="Requester Network Inc",
            info_prefixes4=100,
            info_prefixes6=50,
            irr_as_set="AS-REQUESTER",
            policy_general="Open",
        )
        NetworkContact.objects.create(
            net=cls.peeringdb_network,
            name="NOC",
            email="noc@requester.example",
            role="Technical",
        )
        cls.affiliated_pdb_network = Network.objects.create(
            id=2,
            org=cls.org,
            asn=4199999990,
            name="Affiliated AS",
            name_long="Affiliated AS Corp",
            info_prefixes4=200,
            info_prefixes6=100,
            irr_as_set="AS-AFFILIATED",
            policy_general="Selective",
        )
        cls.pdb_ix = PeeringDBIX.objects.create(id=1, name="Test IX", org=cls.org)
        cls.ixlan = IXLan.objects.create(id=42, ix=cls.pdb_ix, name="Test IX LAN")
        cls.ix = InternetExchange.objects.create(
            name="Test IX",
            slug="test-ix",
            local_autonomous_system=cls.affiliated_as,
            peeringdb_ixlan=cls.ixlan,
        )
        cls.connection = Connection.objects.create(
            internet_exchange_point=cls.ix,
            ipv4_address="192.0.2.254/24",
            ipv6_address="2001:db8::ffff/64",
        )
        NetworkIXLan.objects.create(
            asn=4199999991,
            net=cls.peeringdb_network,
            ixlan=cls.ixlan,
            ipaddr4="192.0.2.1",
            ipaddr6="2001:db8::1",
            speed=10000,
        )
        NetworkIXLan.objects.create(
            asn=4199999990,
            net=cls.affiliated_pdb_network,
            ixlan=cls.ixlan,
            ipaddr4="192.0.2.254",
            ipaddr6="2001:db8::ffff",
            speed=10000,
        )
        cls.facility = Facility.objects.create(id=17, name="Test Facility", org=cls.org)

    def setUp(self):
        super().setUp()
        self.user.preferences.set("context.as", self.affiliated_as.pk, commit=True)
        # Avoid polluting next tests
        self.addCleanup(self.user.preferences.delete, "context", commit=True)

    def _create_pending_request(self):
        pr = PeeringRequest.objects.create(
            requesting_asn=4199999991,
            local_autonomous_system=self.affiliated_as,
            request_type=PeeringRequestType.PUBLIC_PEERING,
        )
        RequestedSession.objects.create(
            peering_request=pr,
            ixp_connection=self.connection,
            ip_address="192.0.2.1/24",
        )
        return pr


class PortalAffiliatedViewTest(PortalAPITestMixin, APITestCase):
    def test_affiliated_as(self):
        url = reverse("peering-api:portal:affiliated")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["asn"], 4199999990)
        self.assertEqual(response.data["name"], "Affiliated AS")

    def test_no_affiliated_as_returns_422(self):
        self.user.preferences.delete("context", commit=True)
        url = reverse("peering-api:portal:affiliated")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)


class PortalNetworkViewTest(PortalAPITestMixin, APITestCase):
    def test_network_lookup_valid_asn(self):
        url = reverse("peering-api:portal:network", kwargs={"asn": 4199999991})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["asn"], 4199999991)
        self.assertEqual(response.data["name"], "Requester Network")
        self.assertEqual(response.data["info_prefixes4"], 100)
        self.assertGreaterEqual(len(response.data["contacts"]), 1)

    def test_network_lookup_unknown_asn(self):
        url = reverse("peering-api:portal:network", kwargs={"asn": 99999})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_network_lookup_null_prefixes(self):
        # PeeringDB networks may leave the prefix counts blank
        Network.objects.create(id=3, org=self.org, asn=4199999992, name="No Limits Net")
        url = reverse("peering-api:portal:network", kwargs={"asn": 4199999992})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["info_prefixes4"])
        self.assertIsNone(response.data["info_prefixes6"])


class PortalLocationViewTest(PortalAPITestMixin, APITestCase):
    def test_locations_shared_ixps(self):
        url = reverse("peering-api:portal:locations")
        response = self.client.get(url, {"asn": 4199999991}, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["locations"]), 1)
        loc = response.data["locations"][0]
        self.assertEqual(loc["location"], "pdb:ix:42")
        self.assertEqual(loc["peering_type"], "public")
        self.assertGreaterEqual(len(loc["sessions"]), 1)

    def _add_second_shared_ixp(self):
        ixlan = IXLan.objects.create(id=43, ix=self.pdb_ix, name="Test IX LAN 2")
        ix = InternetExchange.objects.create(
            name="Test IX 2",
            slug="test-ix-2",
            local_autonomous_system=self.affiliated_as,
            peeringdb_ixlan=ixlan,
        )
        Connection.objects.create(internet_exchange_point=ix, ipv4_address="192.0.3.254/24")
        NetworkIXLan.objects.create(
            asn=4199999991, net=self.peeringdb_network, ixlan=ixlan, ipaddr4="192.0.3.1", speed=10000
        )
        NetworkIXLan.objects.create(
            asn=4199999990, net=self.affiliated_pdb_network, ixlan=ixlan, ipaddr4="192.0.3.254", speed=10000
        )

    def test_locations_multiple_shared_ixps(self):
        self._add_second_shared_ixp()
        url = reverse("peering-api:portal:locations")
        response = self.client.get(url, {"asn": 4199999991}, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_location = {loc["location"]: loc for loc in response.data["locations"]}
        self.assertIn("pdb:ix:42", by_location)
        self.assertIn("pdb:ix:43", by_location)
        self.assertGreaterEqual(len(by_location["pdb:ix:43"]["sessions"]), 1)

    def test_locations_queries_do_not_scale_with_ixps(self):
        url = reverse("peering-api:portal:locations")
        # Warm-up request to fill caches (content types), then measure with a single shared IXP
        self.client.get(url, {"asn": 4199999991}, **self.header)
        with CaptureQueriesContext(db_connection) as baseline:
            self.client.get(url, {"asn": 4199999991}, **self.header)

        self._add_second_shared_ixp()
        with CaptureQueriesContext(db_connection) as with_two_ixps:
            self.client.get(url, {"asn": 4199999991}, **self.header)

        self.assertEqual(len(with_two_ixps.captured_queries), len(baseline.captured_queries))

    def test_locations_unknown_asn(self):
        url = reverse("peering-api:portal:locations")
        response = self.client.get(url, {"asn": 64501}, **self.header)
        # ASN 64501 doesn't exist in PeeringDB cache
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_locations_rejects_invalid_params(self):
        url = reverse("peering-api:portal:locations")

        # Missing asn
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Out-of-range asn
        response = self.client.get(url, {"asn": 0}, **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Unknown location_type
        response = self.client.get(url, {"asn": 4199999991, "location_type": "carrier"}, **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PortalSessionSubmitTest(PortalAPITestMixin, APITestCase):
    def test_submit_rejects_invalid_payloads(self):
        url = reverse("peering-api:portal:sessions")
        session = {"local_ip": "192.0.2.1/24", "location": "pdb:ix:42", "peer_ip": "192.0.2.254"}

        # Empty session list
        data = {"local_asn": 4199999991, "peer_type": "public", "sessions": []}
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Unknown peering type
        data = {"local_asn": 4199999991, "peer_type": "carrier", "sessions": [session]}
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Out-of-range ASN
        data = {"local_asn": 0, "peer_type": "public", "sessions": [session]}
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("local_asn", response.data)

        self.assertEqual(PeeringRequest.objects.count(), 0)

    def test_no_affiliated_as_returns_422(self):
        self.user.preferences.delete("context", commit=True)
        url = reverse("peering-api:portal:sessions")
        data = {
            "local_asn": 4199999991,
            "peer_type": "public",
            "sessions": [{"local_ip": "192.0.2.1/24", "location": "pdb:ix:42", "peer_ip": "192.0.2.254"}],
        }
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_submit_peering_request(self):
        url = reverse("peering-api:portal:sessions")
        data = {
            "local_asn": 4199999991,
            "peer_type": "public",
            "email": "noc@requester.example",
            "sessions": [
                {
                    "local_ip": "192.0.2.1/24",
                    "location": "pdb:ix:42",
                    "peer_ip": "192.0.2.254",
                },
                {
                    "local_ip": "2001:db8::1/64",
                    "location": "pdb:ix:42",
                    "peer_ip": "2001:db8::ffff",
                    "session_secret": "s3cret",
                },
            ],
        }
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("request_id", response.data)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["sessions_count"], 2)

        # Verify PeeringRequest was created
        pr = PeeringRequest.objects.get(tracking_id=response.data["request_id"])
        self.assertEqual(pr.requesting_asn, 4199999991)
        self.assertEqual(pr.request_type, PeeringRequestType.PUBLIC_PEERING)
        self.assertEqual(pr.requested_sessions.count(), 2)

        # Verify no BGP sessions created
        self.assertEqual(InternetExchangePeeringSession.objects.count(), 0)

    def test_submit_duplicate_request_notation_insensitive(self):
        url = reverse("peering-api:portal:sessions")
        data = {
            "local_asn": 4199999991,
            "peer_type": "public",
            "sessions": [
                {
                    "local_ip": "2001:db8::1/64",
                    "location": "pdb:ix:42",
                    "peer_ip": "2001:db8::ffff",
                }
            ],
        }
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Same host address written differently (uppercase, no prefix length)
        data["sessions"][0]["local_ip"] = "2001:DB8::1"
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "duplicate_pending")
        self.assertIn("2001:db8::1", response.data["conflicting_ips"])
        self.assertEqual(PeeringRequest.objects.count(), 1)

    def test_submit_duplicate_ips_in_payload(self):
        url = reverse("peering-api:portal:sessions")
        data = {
            "local_asn": 4199999991,
            "peer_type": "public",
            "sessions": [
                {
                    "local_ip": "192.0.2.1/24",
                    "location": "pdb:ix:42",
                    "peer_ip": "192.0.2.254",
                },
                {
                    "local_ip": "192.0.2.1",
                    "location": "pdb:ix:42",
                    "peer_ip": "192.0.2.254",
                },
            ],
        }
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PeeringRequest.objects.count(), 0)

    def test_submit_same_ip_to_multiple_connections(self):
        # The same requester IP towards two operator connections is a valid setup
        Connection.objects.create(
            internet_exchange_point=self.ix,
            ipv4_address="192.0.2.253/24",
        )

        url = reverse("peering-api:portal:sessions")
        data = {
            "local_asn": 4199999991,
            "peer_type": "public",
            "sessions": [
                {
                    "local_ip": "192.0.2.1/24",
                    "location": "pdb:ix:42",
                    "peer_ip": "192.0.2.254",
                },
                {
                    "local_ip": "192.0.2.1/24",
                    "location": "pdb:ix:42",
                    "peer_ip": "192.0.2.253",
                },
            ],
        }
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["sessions_count"], 2)

    def test_submit_unknown_asn(self):
        url = reverse("peering-api:portal:sessions")
        data = {
            "local_asn": 99999,
            "peer_type": "public",
            "sessions": [
                {
                    "local_ip": "10.0.0.1/24",
                    "location": "pdb:ix:42",
                    "peer_ip": "192.0.2.254",
                }
            ],
        }
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_rejects_existing_ixp_session(self):
        # The session stores a bare host IP; the requester submits it with a prefix length
        requester_as = AutonomousSystem.objects.create(asn=4199999991, name="Requester Network")
        InternetExchangePeeringSession.objects.create(
            autonomous_system=requester_as,
            ixp_connection=self.connection,
            ip_address="192.0.2.1",
        )

        url = reverse("peering-api:portal:sessions")
        data = {
            "local_asn": 4199999991,
            "peer_type": "public",
            "sessions": [
                {
                    "local_ip": "192.0.2.1/24",
                    "location": "pdb:ix:42",
                    "peer_ip": "192.0.2.254",
                }
            ],
        }
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "already_configured")
        self.assertIn("192.0.2.1", response.data["conflicting_ips"])

        # No PeeringRequest should have been created
        self.assertEqual(PeeringRequest.objects.count(), 0)

    def test_submit_rejects_existing_direct_session(self):
        requester_as = AutonomousSystem.objects.create(asn=4199999991, name="Requester Network")
        DirectPeeringSession.objects.create(
            local_autonomous_system=self.affiliated_as,
            autonomous_system=requester_as,
            relationship=Relationship.objects.create(name="Test", slug="test"),
            ip_address="192.0.2.2",
        )

        url = reverse("peering-api:portal:sessions")
        data = {
            "local_asn": 4199999991,
            "peer_type": "private",
            "sessions": [
                {
                    "local_ip": "192.0.2.2/30",
                    "peer_ip": "192.0.2.1/30",
                    "location": "pdb:fac:17",
                }
            ],
        }
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "already_configured")
        self.assertIn("192.0.2.2", response.data["conflicting_ips"])
        self.assertEqual(PeeringRequest.objects.count(), 0)

    def test_submit_requires_peer_ip(self):
        # `peer_ip` is enforced by the serializer, so the error is per-session
        url = reverse("peering-api:portal:sessions")
        data = {
            "local_asn": 4199999991,
            "peer_type": "private",
            "sessions": [{"local_ip": "192.0.2.1/30", "location": "pdb:fac:17"}],
        }
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("peer_ip", response.data["sessions"][0])
        self.assertEqual(PeeringRequest.objects.count(), 0)

    def test_submit_private_requires_prefix_length(self):
        url = reverse("peering-api:portal:sessions")
        data = {
            "local_asn": 4199999991,
            "peer_type": "private",
            "sessions": [{"local_ip": "192.0.2.1", "peer_ip": "192.0.2.2/30", "location": "pdb:fac:17"}],
        }
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("local_ip", response.data)

        data["sessions"] = [{"local_ip": "192.0.2.1/30", "peer_ip": "192.0.2.2", "location": "pdb:fac:17"}]
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("peer_ip", response.data)

        self.assertEqual(PeeringRequest.objects.count(), 0)

    def test_submit_private_with_peer_ip(self):
        url = reverse("peering-api:portal:sessions")
        data = {
            "local_asn": 4199999991,
            "peer_type": "private",
            "sessions": [
                {
                    "local_ip": "192.0.2.1/30",
                    "peer_ip": "192.0.2.2/30",
                    "location": "pdb:fac:17",
                }
            ],
        }
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        pr = PeeringRequest.objects.get(tracking_id=response.data["request_id"])
        session = pr.requested_sessions.get()
        self.assertEqual(str(session.peer_ip_address), "192.0.2.2/30")
        self.assertEqual(session.peeringdb_facility, self.facility)


class PortalAuthTest(PortalAPITestMixin, APITestCase):
    def test_unauthenticated_access_denied(self):
        url = reverse("peering-api:portal:network", kwargs={"asn": 4199999991})
        response = self.client.get(url)
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_user_without_permission_denied(self):
        user = User.objects.create(username="noperm", is_staff=False)
        token = Token.objects.create(user=user)
        header = {"HTTP_AUTHORIZATION": f"Token {token.key}"}
        url = reverse("peering-api:portal:network", kwargs={"asn": 4199999991})
        response = self.client.get(url, **header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_with_permissions_allowed(self):
        # A regular user (not superuser) holding the documented permissions must get through;
        # superusers pass `has_perm` unconditionally and would mask a broken permission check
        user = User.objects.create(username="portal", is_staff=False)
        user.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="peering", codename__in=("add_peeringrequest", "change_peeringrequest")
            )
        )
        token = Token.objects.create(user=user)
        header = {"HTTP_AUTHORIZATION": f"Token {token.key}"}
        url = reverse("peering-api:portal:network", kwargs={"asn": 4199999991})
        response = self.client.get(url, **header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PortalStatusAndCancelTest(PortalAPITestMixin, APITestCase):
    def test_get_status_by_tracking_id(self):
        pr = self._create_pending_request()
        url = reverse(
            "peering-api:portal:sessions-detail",
            kwargs={"request_id": str(pr.tracking_id)},
        )
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["request_id"], str(pr.tracking_id))
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["local_asn"], 4199999991)
        self.assertGreaterEqual(len(response.data["sessions"]), 1)
        # A session with no peer IP set serializes as null, not an error
        self.assertIsNone(response.data["sessions"][0]["peer_ip"])

    def test_get_status_unknown_tracking_id(self):
        url = reverse(
            "peering-api:portal:sessions-detail",
            kwargs={"request_id": "00000000-0000-0000-0000-000000000000"},
        )
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_requests_by_asn(self):
        self._create_pending_request()
        url = reverse("peering-api:portal:sessions")
        response = self.client.get(url, {"asn": 4199999991}, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["requests"]), 1)

    def test_list_requests_filter_by_request_id(self):
        pr = self._create_pending_request()
        url = reverse("peering-api:portal:sessions")
        response = self.client.get(url, {"asn": 4199999991, "request_id": str(pr.tracking_id)}, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["requests"]), 1)

    def test_list_requests_invalid_request_id(self):
        url = reverse("peering-api:portal:sessions")
        response = self.client.get(url, {"asn": 4199999991, "request_id": "garbage"}, **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_pending_request(self):
        pr = self._create_pending_request()
        url = reverse(
            "peering-api:portal:sessions-detail",
            kwargs={"request_id": str(pr.tracking_id)},
        )
        response = self.client.delete(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PeeringRequestStatus.CANCELLED)

    def test_cancel_accepted_request_fails(self):
        pr = self._create_pending_request()
        pr.status = PeeringRequestStatus.ACCEPTED
        pr.save()
        url = reverse(
            "peering-api:portal:sessions-detail",
            kwargs={"request_id": str(pr.tracking_id)},
        )
        response = self.client.delete(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


class PortalSchemaTest(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.schema = SchemaGenerator().get_schema(request=None, public=True)

    def _properties(self, component):
        return self.schema["components"]["schemas"][component]["properties"]

    def _param_names(self, path):
        return {p["name"] for p in self.schema["paths"][path]["get"]["parameters"]}

    def test_nullable_fields_declared(self):
        network = self._properties("PortalNetwork")
        self.assertTrue(network["info_prefixes4"].get("nullable"))
        self.assertTrue(network["info_prefixes6"].get("nullable"))
        self.assertTrue(self._properties("PortalRequestedSessionStatus")["peer_ip"].get("nullable"))

    def test_query_parameters_declared(self):
        locations = self._param_names("/api/peering/portal/locations")
        self.assertIn("asn", locations)
        self.assertIn("location_type", locations)

        sessions = self._param_names("/api/peering/portal/sessions")
        self.assertIn("asn", sessions)
        self.assertIn("request_id", sessions)
