from django.test import TestCase

from net.enums import ConnectionStatus
from net.forms import ConnectionForm


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
