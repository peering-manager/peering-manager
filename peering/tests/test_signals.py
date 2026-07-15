from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from bgp.models import Relationship
from net.models import Connection

from ..enums import PeeringRequestType
from ..models import (
    AutonomousSystem,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    PeeringRequest,
    RequestedSession,
)


class PeeringRequestConflictSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.local_as = AutonomousSystem.objects.create(asn=64500, name="Local", affiliated=True)
        cls.peer_as = AutonomousSystem.objects.create(asn=64510, name="Peer")
        cls.ixp = InternetExchange.objects.create(local_autonomous_system=cls.local_as, name="Test IX", slug="test-ix")
        cls.connection = Connection.objects.create(vlan=2000, internet_exchange_point=cls.ixp)
        peering_request = PeeringRequest.objects.create(
            requesting_asn=64510,
            local_autonomous_system=cls.local_as,
            request_type=PeeringRequestType.PUBLIC_PEERING,
        )
        RequestedSession.objects.create(
            peering_request=peering_request,
            ixp_connection=cls.connection,
            ip_address="192.0.2.1/24",
        )

    @override_settings(PEERING_REQUEST_BLOCKS_SESSION_CREATION=True)
    def test_blocking_scopes_ixp_by_connection(self):
        # Same connection and IP as the pending request: blocked (the bare IP still matches the /24 on host)
        with self.assertRaises(ValidationError):
            InternetExchangePeeringSession.objects.create(
                autonomous_system=self.peer_as,
                ixp_connection=self.connection,
                ip_address="192.0.2.1",
            )
        self.assertFalse(InternetExchangePeeringSession.objects.exists())

        # Same IP on another connection is free: the reservation is per (connection, IP)
        other_connection = Connection.objects.create(vlan=2001, internet_exchange_point=self.ixp)
        session = InternetExchangePeeringSession.objects.create(
            autonomous_system=self.peer_as,
            ixp_connection=other_connection,
            ip_address="192.0.2.1",
        )
        self.assertIsNotNone(session.pk)

    @override_settings(PEERING_REQUEST_BLOCKS_SESSION_CREATION=True)
    def test_blocking_setting_scopes_direct_sessions_by_asn(self):
        relationship = Relationship.objects.create(name="Test", slug="test")

        # Same IP, same ASN as the pending request: blocked
        with self.assertRaises(ValidationError):
            DirectPeeringSession.objects.create(
                local_autonomous_system=self.local_as,
                autonomous_system=self.peer_as,
                relationship=relationship,
                ip_address="192.0.2.1/24",
            )

        # Unrelated peers legitimately reuse interconnect IP space: not blocked
        other_as = AutonomousSystem.objects.create(asn=64520, name="Other")
        session = DirectPeeringSession.objects.create(
            local_autonomous_system=self.local_as,
            autonomous_system=other_as,
            relationship=relationship,
            ip_address="192.0.2.1/24",
        )
        self.assertIsNotNone(session.pk)

    @override_settings(PEERING_REQUEST_BLOCKS_SESSION_CREATION=False)
    def test_default_setting_warns(self):
        ip_address = "192.0.2.1/24"
        with self.assertLogs("peering.manager.peering", level="WARNING") as log:
            session = InternetExchangePeeringSession.objects.create(
                autonomous_system=self.peer_as,
                ixp_connection=self.connection,
                ip_address=ip_address,
            )

        self.assertIsNotNone(session)
        self.assertEqual(len(log.records), 1)
        self.assertIn(
            f"Cannot create session for {ip_address}: already covered by 1 pending peering request",
            log.records[0].getMessage(),
        )
