from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

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

from ..enums import *
from ..models import *


class PortalAPITestMixin:
    @classmethod
    def setUpTestData(cls):
        # This test relies on the fact that ASNs must be public, so we use high 32-bit
        # ASNs unlikely to be allocated to actual networks today
        cls.org = Organization.objects.create(id=1, name="Test Org")
        cls.affiliated_as = AutonomousSystem.objects.create(
            asn=4199999990, name="Affiliated AS", affiliated=True
        )
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

    def test_locations_no_overlap(self):
        url = reverse("peering-api:portal:locations")
        response = self.client.get(url, {"asn": 64501}, **self.header)
        # ASN 64501 doesn't exist in PeeringDB cache
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_locations_missing_asn_param(self):
        url = reverse("peering-api:portal:locations")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PortalSessionCreateViewTest(PortalAPITestMixin, APITestCase):
    def test_submit_peering_request(self):
        url = reverse("peering-api:portal:sessions-create")
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

    def test_submit_duplicate_request(self):
        url = reverse("peering-api:portal:sessions-create")
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
        # First submission should succeed
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Duplicate should be rejected
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_submit_unknown_asn(self):
        url = reverse("peering-api:portal:sessions-create")
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
        # Create an existing BGP session with the IP the requester is about to ask for
        requester_as = AutonomousSystem.objects.create(
            asn=4199999991, name="Requester Network"
        )
        InternetExchangePeeringSession.objects.create(
            autonomous_system=requester_as,
            ixp_connection=self.connection,
            ip_address="192.0.2.1/24",
        )

        url = reverse("peering-api:portal:sessions-create")
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
        self.assertIn("existing_session_ips", response.data)
        self.assertIn("192.0.2.1/24", response.data["existing_session_ips"])

        # No PeeringRequest should have been created
        self.assertEqual(PeeringRequest.objects.count(), 0)

    def test_submit_private_requires_peer_ip(self):
        url = reverse("peering-api:portal:sessions-create")
        data = {
            "local_asn": 4199999991,
            "peer_type": "private",
            "sessions": [{"local_ip": "192.0.2.1/30", "location": "17"}],
        }
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("peer_ip", response.data)
        self.assertEqual(PeeringRequest.objects.count(), 0)

    def test_submit_private_with_peer_ip(self):
        url = reverse("peering-api:portal:sessions-create")
        data = {
            "local_asn": 4199999991,
            "peer_type": "private",
            "sessions": [
                {
                    "local_ip": "192.0.2.1/30",
                    "peer_ip": "192.0.2.2/30",
                    "location": "17",
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


class PeeringRequestAcceptRejectTest(PortalAPITestMixin, APITestCase):
    def _create_peering_request(self):
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

    def test_accept_request_auto_creates_as(self):
        # Ensure the AutonomousSystem does not exist before acceptance
        self.assertFalse(AutonomousSystem.objects.filter(asn=4199999991).exists())

        pr = self._create_peering_request()
        url = reverse("peering-api:peeringrequest-accept", kwargs={"pk": pr.pk})
        response = self.client.post(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "accepted")
        pr.refresh_from_db()
        self.assertEqual(pr.status, PeeringRequestStatus.ACCEPTED)

        # AutonomousSystem record should have been created from PeeringDB data
        autonomous_system = AutonomousSystem.objects.get(asn=4199999991)
        self.assertEqual(autonomous_system.name, "Requester Network")
        self.assertEqual(autonomous_system.ipv4_max_prefixes, 100)
        self.assertEqual(autonomous_system.ipv6_max_prefixes, 50)

    def test_reject_request_with_comment(self):
        pr = self._create_peering_request()
        url = reverse("peering-api:peeringrequest-reject", kwargs={"pk": pr.pk})
        response = self.client.post(
            url, {"comment": "Not peering at this time"}, format="json", **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PeeringRequestStatus.REFUSED)
        self.assertEqual(pr.decision_comment, "Not peering at this time")

    def test_reject_already_accepted(self):
        pr = self._create_peering_request()
        pr.status = PeeringRequestStatus.ACCEPTED
        pr.save()
        url = reverse("peering-api:peeringrequest-reject", kwargs={"pk": pr.pk})
        response = self.client.post(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_per_session_accept(self):
        pr = self._create_peering_request()
        session = pr.requested_sessions.first()
        url = reverse("peering-api:requestedsession-accept", kwargs={"pk": session.pk})
        response = self.client.post(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, RequestedSessionStatus.ACCEPTED)

    def test_per_session_reject(self):
        pr = self._create_peering_request()
        session = pr.requested_sessions.first()
        url = reverse("peering-api:requestedsession-reject", kwargs={"pk": session.pk})
        response = self.client.post(
            url, {"comment": "No IPv4"}, format="json", **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, RequestedSessionStatus.REJECTED)
        self.assertEqual(session.rejection_comment, "No IPv4")


class PortalStatusAndCancelTest(PortalAPITestMixin, APITestCase):
    def _create_request(self):
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

    def test_get_status_by_tracking_id(self):
        pr = self._create_request()
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

    def test_get_status_invalid_uuid(self):
        url = reverse(
            "peering-api:portal:sessions-detail",
            kwargs={"request_id": "00000000-0000-0000-0000-000000000000"},
        )
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_requests_by_asn(self):
        self._create_request()
        url = reverse("peering-api:portal:sessions-list")
        response = self.client.get(url, {"asn": 4199999991}, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["requests"]), 1)

    def test_cancel_pending_request(self):
        pr = self._create_request()
        url = reverse(
            "peering-api:portal:sessions-detail",
            kwargs={"request_id": str(pr.tracking_id)},
        )
        response = self.client.delete(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PeeringRequestStatus.CANCELLED)

    def test_cancel_accepted_request_fails(self):
        pr = self._create_request()
        pr.status = PeeringRequestStatus.ACCEPTED
        pr.save()
        url = reverse(
            "peering-api:portal:sessions-detail",
            kwargs={"request_id": str(pr.tracking_id)},
        )
        response = self.client.delete(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
