from django.urls import reverse
from rest_framework import status

from net.enums import ConnectionStatus
from net.models import Connection
from peering.enums import DeviceStatus
from peering.models import AutonomousSystem, InternetExchange, Router
from utils.testing import APITestCase, StandardAPITestCases


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("net-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ConnectionTest(StandardAPITestCases.View):
    model = Connection
    brief_fields = [
        "id",
        "url",
        "display",
        "name",
        "mac_address",
        "ipv6_address",
        "ipv4_address",
    ]
    bulk_update_data = {"status": ConnectionStatus.DISABLED}

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
        Connection.objects.bulk_create(
            [
                Connection(
                    status=ConnectionStatus.ENABLED,
                    vlan=2000,
                    mac_address="c8:da:66:91:3f:08",
                    ipv6_address="2001:db8:10::/64",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
                Connection(
                    status=ConnectionStatus.ENABLED,
                    vlan=2000,
                    mac_address="7D-54-E0-B5-20-17",
                    ipv6_address="2001:db8:10::f/64",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
                Connection(
                    status=ConnectionStatus.ENABLED,
                    vlan=2000,
                    ipv6_address="2001:db8:10::ff/64",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
            ]
        )
        cls.create_data = [
            {
                "status": ConnectionStatus.ENABLED,
                "vlan": 2001,
                "mac_address": "790e.0091.9c97",
                "ipv6_address": "2001:db8:10::1/64",
                "internet_exchange_point": internet_exchange_point.pk,
                "router": router.pk,
            },
            {
                "status": ConnectionStatus.ENABLED,
                "vlan": 2002,
                "mac_address": "30ad6e2f44c3",
                "ipv4_address": "192.0.2.2/24",
                "internet_exchange_point": internet_exchange_point.pk,
                "router": router.pk,
            },
            {
                "status": ConnectionStatus.DISABLED,
                "mac_address": "30ad.742f.44c3",
                "ipv6_address": "2001:db8:10::3/64",
                "ipv4_address": "192.0.2.3",
                "internet_exchange_point": internet_exchange_point.pk,
                "router": router.pk,
            },
        ]
