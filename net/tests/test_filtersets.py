from django.test import TestCase

from devices.enums import DeviceStatus
from devices.models import Router
from peering.models import AutonomousSystem, InternetExchange
from utils.testing import BaseFilterSetTests

from ..enums import *
from ..filtersets import *
from ..models import *


class BFDTestCase(TestCase, BaseFilterSetTests):
    queryset = BFD.objects.all()
    filterset = BFDFilterSet

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

    def test_q(self):
        params = {"q": "default"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "Double"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "timers"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"q": "foo"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_minimum_transmit_interval(self):
        params = {"minimum_transmit_interval": [300]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"minimum_transmit_interval": [600]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"minimum_transmit_interval__gt": [0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"minimum_transmit_interval__lt": [100]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_minimum_receive_interval(self):
        params = {"minimum_receive_interval": [300]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"minimum_receive_interval": [600]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"minimum_receive_interval__gt": [0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"minimum_receive_interval__lt": [100]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_detection_multiplier(self):
        params = {"detection_multiplier": [3]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"detection_multiplier": [6]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"detection_multiplier__gte": [0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"detection_multiplier__lt": [0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_hold_time(self):
        params = {"hold_time": [0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"hold_time": [600]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"hold_time__gte": [0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"hold_time__lt": [0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)


class ConnectionTestCase(TestCase, BaseFilterSetTests):
    queryset = Connection.objects.all()
    filterset = ConnectionFilterSet

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
                    vlan=2001,
                    ipv6_address="2001:db8:10::1",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                    interface="eth-0/0/0",
                ),
                Connection(
                    status=ConnectionStatus.ENABLED,
                    vlan=2002,
                    ipv4_address="192.0.2.2",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
                Connection(
                    status=ConnectionStatus.DISABLED,
                    ipv6_address="2001:db8:10::3",
                    ipv4_address="192.0.2.3",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
            ]
        )

    def test_q(self):
        params = {"q": "2001:db8:10::1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "192.0.2.2"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "eth-0/0/0"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "eth"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_status(self):
        params = {"status": [ConnectionStatus.ENABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"status": [ConnectionStatus.DISABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"status": [""]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_vlan(self):
        params = {"vlan": [2001]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"vlan": [2001, 2002]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
