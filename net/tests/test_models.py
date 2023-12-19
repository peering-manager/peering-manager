from django.test import TestCase

from peering.enums import DeviceStatus
from peering.models import AutonomousSystem, InternetExchange, Router

from ..enums import *
from ..models import *


class ConnectionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        internet_exchange_point = InternetExchange.objects.create(
            name="Test", slug="test", local_autonomous_system=local_autonomous_system
        )
        router = Router.objects.create(
            name="Test",
            hostname="test.example.com",
            status=DeviceStatus.ENABLED,
            local_autonomous_system=local_autonomous_system,
        )
        cls.connection = Connection(
            status=ConnectionStatus.ENABLED,
            vlan=2001,
            ipv6_address="2001:db8:10::1",
            internet_exchange_point=internet_exchange_point,
            router=router,
        )

    def test_linked_to_peeringdb(self):
        self.assertFalse(self.connection.linked_to_peeringdb)

    def test_link_to_peeringdb(self):
        self.assertIsNone(self.connection.link_to_peeringdb())

    def test__str__(self):
        self.assertEqual("Test on Test", str(self.connection))
        self.connection.router = None
        self.connection.interface = ""
        self.connection.save()
        self.assertEqual("Test", str(self.connection))
        self.connection.internet_exchange_point = None
        self.connection.save()
        self.assertEqual(f"Connection #{self.connection.pk}", str(self.connection))
