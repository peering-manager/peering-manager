from django.test import TestCase
from unittest.mock import patch

from .mock import MockedResponse
from netbox.api import NetBox


class NetBoxTestCase(TestCase):
    @patch(
        "pynetbox.core.query.requests.sessions.Session.get",
        return_value=MockedResponse(
            fixture="netbox/tests/fixtures/netbox_devices.json"
        ),
    )
    def test_get_devices(self, *_):
        devices = NetBox().get_devices()

        self.assertEqual(2, len(devices))
        self.assertEqual("router02.example.net", devices.pop().name)
        self.assertEqual("router01.example.net", devices.pop().name)

    @patch(
        "pynetbox.core.endpoint.RODetailEndpoint.list",
        return_value={
            "get_facts": MockedResponse(
                fixture="netbox/tests/fixtures/netbox_device_facts.json"
            ).json()
        },
    )
    def test_napalm(self, *_):
        facts = NetBox().napalm(1, "get_facts")
        self.assertEqual("router01", facts["hostname"])
