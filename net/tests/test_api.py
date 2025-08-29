from django.urls import reverse
from rest_framework import status

from devices.enums import DeviceStatus
from devices.models import Router
from peering.models import AutonomousSystem, InternetExchange
from utils.testing import APITestCase, APIViewTestCases

from ..enums import *
from ..models import *


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("net-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BFDTest(APIViewTestCases.View):
    model = BFD
    brief_fields = ["id", "url", "display_url", "display", "name", "slug"]
    bulk_update_data = {"description": "Foo"}

    @classmethod
    def setUpTestData(cls):
        BFD.objects.bulk_create(
            [
                BFD(
                    name="Default",
                    slug="default",
                    description="Default timers and detection",
                    minimum_transmit_interval=300,
                    minimum_receive_interval=300,
                    detection_multiplier=3,
                    hold_time=0,
                ),
                BFD(
                    name="Double",
                    slug="double",
                    description="Double timers and detection",
                    minimum_transmit_interval=600,
                    minimum_receive_interval=600,
                    detection_multiplier=6,
                    hold_time=600,
                ),
                BFD(
                    name="Ones",
                    slug="ones",
                    description="All ones",
                    minimum_transmit_interval=1,
                    minimum_receive_interval=1,
                    detection_multiplier=1,
                    hold_time=1,
                ),
            ]
        )
        cls.create_data = [
            {
                "name": "Test 1",
                "slug": "test-1",
                "minimum_transmit_interval": 1000,
                "minimum_receive_interval": 1000,
                "detection_multiplier": 1,
                "hold_time": 0,
            },
            {
                "name": "Test 2",
                "slug": "test-2",
                "minimum_transmit_interval": 2000,
                "minimum_receive_interval": 2000,
                "detection_multiplier": 2,
                "hold_time": 0,
            },
            {
                "name": "Test 3",
                "slug": "test-3",
                "minimum_transmit_interval": 3000,
                "minimum_receive_interval": 3000,
                "detection_multiplier": 3,
                "hold_time": 0,
            },
        ]


class ConnectionTest(APIViewTestCases.View):
    model = Connection
    brief_fields = [
        "id",
        "url",
        "display_url",
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
