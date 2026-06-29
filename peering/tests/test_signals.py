from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from net.models import Connection

from ..enums import PeeringRequestType
from ..models import (
    AutonomousSystem,
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
    def test_blocking_setting_raises(self):
        with self.assertRaises(ValidationError):
            InternetExchangePeeringSession.objects.create(
                autonomous_system=self.peer_as,
                ixp_connection=self.connection,
                ip_address="192.0.2.1/24",
            )
        self.assertFalse(InternetExchangePeeringSession.objects.filter(ip_address="192.0.2.1/24").exists())

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
