from net.filters import ConnectionFilterSet
from net.models import Connection
from peering.enums import DeviceState
from peering.models import AutonomousSystem, InternetExchange, Router
from utils.testing import StandardTestCases


class ConnectionTestCase(StandardTestCases.Filters):
    model = Connection
    filter = ConnectionFilterSet

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
            device_state=DeviceState.ENABLED,
            local_autonomous_system=local_autonomous_system,
        )
        Connection.objects.bulk_create(
            [
                Connection(
                    vlan=2001,
                    ipv6_address="2001:db8:10::1",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
                Connection(
                    vlan=2002,
                    ipv4_address="192.0.2.2",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
                Connection(
                    ipv6_address="2001:db8:10::3",
                    ipv4_address="192.0.2.3",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
            ]
        )

    def test_q(self):
        params = {"q": "2001:db8:10::1"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)
        params = {"q": "192.0.2.2"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)

    def test_vlan(self):
        params = {"vlan": [2001]}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)
        params = {"vlan": [2001, 2002]}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 2)
