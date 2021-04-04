from django.test import TestCase

from net.enums import ConnectionState
from net.forms import ConnectionForm
from net.models import Connection


class ConnectionTest(TestCase):
    def test_connection_form(self):
        test = ConnectionForm(
            data={
                "state": ConnectionState.ENABLED,
                "vlan": 2000,
                "ipv6_address": "2001:db8::1",
                "ipv4_address": "",
                "internet_exchange_point": None,
                "router": None,
                "description": "",
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())

        test = ConnectionForm(
            data={
                "state": ConnectionState.ENABLED,
                "vlan": 2000,
                "ipv6_address": "",
                "ipv4_address": "192.0.2.1",
                "internet_exchange_point": None,
                "router": None,
                "description": "",
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())

        test = ConnectionForm(
            data={
                "state": ConnectionState.DISABLED,
                "vlan": 2000,
                "ipv6_address": "2001:db8::1",
                "ipv4_address": "192.0.2.1",
                "internet_exchange_point": None,
                "router": None,
                "description": "",
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())
