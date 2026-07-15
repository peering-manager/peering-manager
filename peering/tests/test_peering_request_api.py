from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from net.models import Connection
from utils.testing import APITestCase

from ..enums import PeeringRequestStatus, PeeringRequestType, RequestedSessionStatus
from ..models import (
    AutonomousSystem,
    InternetExchangePeeringSession,
    PeeringRequest,
    RequestedSession,
)
from .test_portal_api import PortalAPITestMixin


class PeeringRequestAcceptRejectTest(PortalAPITestMixin, APITestCase):
    def test_accept_request_auto_creates_as(self):
        # Ensure the AutonomousSystem does not exist before acceptance
        self.assertFalse(AutonomousSystem.objects.filter(asn=4199999991).exists())

        pr = self._create_pending_request()
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

    @override_settings(PEERING_REQUEST_BLOCKS_SESSION_CREATION=True)
    def test_accept_request_with_blocking_setting(self):
        # The request's own pending session must not block its acceptance
        pr = self._create_pending_request()
        url = reverse("peering-api:peeringrequest-accept", kwargs={"pk": pr.pk})
        response = self.client.post(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PeeringRequestStatus.ACCEPTED)
        session = pr.requested_sessions.get()
        self.assertEqual(session.status, RequestedSessionStatus.ACCEPTED)
        self.assertTrue(
            InternetExchangePeeringSession.objects.filter(
                ixp_connection=self.connection, ip_address="192.0.2.1"
            ).exists()
        )

    @override_settings(PEERING_REQUEST_BLOCKS_SESSION_CREATION=True)
    def test_accept_request_with_blocking_setting_same_ip_multiple_connections(self):
        # Sibling sessions of the same request must not block each other either
        connection2 = Connection.objects.create(internet_exchange_point=self.ix, ipv4_address="192.0.2.253/24")
        pr = self._create_pending_request()
        RequestedSession.objects.create(peering_request=pr, ixp_connection=connection2, ip_address="192.0.2.1/24")
        url = reverse("peering-api:peeringrequest-accept", kwargs={"pk": pr.pk})
        response = self.client.post(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(InternetExchangePeeringSession.objects.count(), 2)
        self.assertEqual(pr.requested_sessions.filter(status=RequestedSessionStatus.ACCEPTED).count(), 2)

    @override_settings(PEERING_REQUEST_BLOCKS_SESSION_CREATION=True)
    def test_accept_request_blocked_by_other_pending_request(self):
        # A pending request from another network covering the same IP still blocks
        pr = self._create_pending_request()
        other = PeeringRequest.objects.create(
            requesting_asn=4199999992,
            local_autonomous_system=self.affiliated_as,
            request_type=PeeringRequestType.PUBLIC_PEERING,
        )
        RequestedSession.objects.create(
            peering_request=other,
            ixp_connection=self.connection,
            ip_address="192.0.2.1/24",
        )
        url = reverse("peering-api:peeringrequest-accept", kwargs={"pk": pr.pk})
        response = self.client.post(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session = pr.requested_sessions.get()
        self.assertEqual(session.status, RequestedSessionStatus.REJECTED)
        self.assertIn("Auto-rejected", session.rejection_comment)
        self.assertEqual(InternetExchangePeeringSession.objects.count(), 0)

    def test_reject_request_with_comment(self):
        pr = self._create_pending_request()
        url = reverse("peering-api:peeringrequest-reject", kwargs={"pk": pr.pk})
        response = self.client.post(url, {"comment": "Not peering at this time"}, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PeeringRequestStatus.REFUSED)
        self.assertEqual(pr.decision_comment, "Not peering at this time")

    def test_reject_already_accepted(self):
        pr = self._create_pending_request()
        pr.status = PeeringRequestStatus.ACCEPTED
        pr.save()
        url = reverse("peering-api:peeringrequest-reject", kwargs={"pk": pr.pk})
        response = self.client.post(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(PEERING_REQUEST_BLOCKS_SESSION_CREATION=True)
    def test_per_session_accept(self):
        pr = self._create_pending_request()
        session = pr.requested_sessions.first()
        url = reverse("peering-api:requestedsession-accept", kwargs={"pk": session.pk})
        response = self.client.post(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, RequestedSessionStatus.ACCEPTED)

    def test_per_session_accept_private_without_relationship(self):
        # Accepting a private session before the operator sets a relationship must be a clean 400
        pr = PeeringRequest.objects.create(
            requesting_asn=4199999991,
            local_autonomous_system=self.affiliated_as,
            request_type=PeeringRequestType.PRIVATE_PEERING,
        )
        session = RequestedSession.objects.create(
            peering_request=pr,
            peeringdb_facility=self.facility,
            ip_address="192.0.2.1/30",
            peer_ip_address="192.0.2.2/30",
        )
        url = reverse("peering-api:requestedsession-accept", kwargs={"pk": session.pk})
        response = self.client.post(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("relationship", response.data["detail"])
        session.refresh_from_db()
        self.assertEqual(session.status, RequestedSessionStatus.PENDING)

    def test_per_session_reject(self):
        pr = self._create_pending_request()
        session = pr.requested_sessions.first()
        url = reverse("peering-api:requestedsession-reject", kwargs={"pk": session.pk})
        response = self.client.post(url, {"comment": "No IPv4"}, format="json", **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, RequestedSessionStatus.REJECTED)
        self.assertEqual(session.rejection_comment, "No IPv4")
