from ipaddress import IPv6Address

from django.db import transaction
from django.urls.exceptions import NoReverseMatch

from net.models import Connection
from peering.enums import DeviceState
from peering.models import AutonomousSystem, InternetExchange, Router
from utils.testing import StandardTestCases


class ConnectionTestCase(StandardTestCases.Views):
    model = Connection

    test_bulk_delete_objects = None
    test_bulk_edit_objects = None
    test_list_objects = None

    @classmethod
    def setUpTestData(cls):
        local_as = AutonomousSystem.objects.create(
            asn=64501, name="Autonomous System 1", affiliated=True
        )
        internet_exchange_point = InternetExchange(
            name="Internet Exchange 1",
            slug="ix-1",
            local_autonomous_system=local_as,
        )
        router = Router(
            name="test",
            hostname="test.example.com",
            device_state=DeviceState.ENABLED,
            local_autonomous_system=local_as,
        )
        Connection.objects.bulk_create(
            [
                Connection(
                    vlan=2001,
                    ipv6_address="2001:db8::1",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
                Connection(
                    vlan=2002,
                    ipv6_address="2001:db8::2",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
                Connection(
                    vlan=2003,
                    ipv6_address="2001:db8::3",
                    internet_exchange_point=internet_exchange_point,
                    router=router,
                ),
            ]
        )

        cls.form_data = {
            "peeringdb_netixlan": None,
            "vlan": 2004,
            "ipv6_address": IPv6Address("2001:db8::4"),
            "ipv4_address": None,
            "internet_exchange_point": internet_exchange_point.pk,
            "router": router.pk,
            "description": "",
            "comments": "",
            "tags": "",
        }
