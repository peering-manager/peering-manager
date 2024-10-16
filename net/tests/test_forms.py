from django.test import TestCase

from ..enums import *
from ..forms import *


class BFDTest(TestCase):
    def test_bfd_form(self):
        test = BFDForm(
            data={
                "name": "Test 1",
                "slug": "test-1",
                "minimum_transmit_interval": 300,
                "minimum_receive_interval": 300,
                "detection_multiplier": 3,
                "hold_time": 0,
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())

        test = BFDForm(
            data={
                "name": "Test 2",
                "slug": "test-2",
                "minimum_transmit_interval": 0,
                "minimum_receive_interval": 0,
                "detection_multiplier": 0,
                "hold_time": 0,
            }
        )
        self.assertFalse(test.is_valid())
        with self.assertRaises(ValueError):
            self.assertFalse(test.save())


class ConnectionTest(TestCase):
    def test_connection_form(self):
        test = ConnectionForm(
            data={
                "status": ConnectionStatus.ENABLED,
                "vlan": 2000,
                "mac_address": "00:1b:77:49:54:fd",
                "ipv6_address": "2001:db8::1",
                "ipv4_address": "",
                "internet_exchange_point": None,
                "router": None,
                "interface": "",
                "description": "",
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())

        test = ConnectionForm(
            data={
                "status": ConnectionStatus.ENABLED,
                "vlan": 2000,
                "ipv6_address": "",
                "ipv4_address": "192.0.2.1",
                "internet_exchange_point": None,
                "router": None,
                "interface": "",
                "description": "",
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())

        test = ConnectionForm(
            data={
                "status": ConnectionStatus.DISABLED,
                "vlan": 2000,
                "ipv6_address": "2001:db8::1",
                "ipv4_address": "192.0.2.1",
                "internet_exchange_point": None,
                "router": None,
                "interface": "",
                "description": "",
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())
