from django.urls import reverse
from rest_framework import status

from net.enums import ConnectionState
from net.models import Connection
from peering.enums import DeviceState
from peering.models import AutonomousSystem, InternetExchange, Router
from utils.testing import APITestCase, StandardAPITestCases


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("net-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ConnectionTest(StandardAPITestCases.View):
    model = Connection
    brief_fields = ["id", "url", "name", "ipv6_address", "ipv4_address"]

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
        Connection.objects.create(
            state=ConnectionState.ENABLED,
            vlan=2000,
            ipv6_address="2001:db8:10::",
            internet_exchange_point=internet_exchange_point,
            router=router,
        )
        cls.create_data = [
            {
                "state": ConnectionState.ENABLED,
                "vlan": 2001,
                "ipv6_address": "2001:db8:10::1",
                "internet_exchange_point": internet_exchange_point.pk,
                "router": router.pk,
            },
            {
                "state": ConnectionState.ENABLED,
                "vlan": 2002,
                "ipv4_address": "192.0.2.2",
                "internet_exchange_point": internet_exchange_point.pk,
                "router": router.pk,
            },
            {
                "state": ConnectionState.DISABLED,
                "ipv6_address": "2001:db8:10::3",
                "ipv4_address": "192.0.2.3",
                "internet_exchange_point": internet_exchange_point.pk,
                "router": router.pk,
            },
        ]
