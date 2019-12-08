import pynetbox

from django.test import TestCase
from unittest.mock import patch

from netbox.api import NetBox
from utils.testing import MockedResponse


class NetBoxTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.netbox = NetBox()
        self.netbox.api = pynetbox.api("http://netbox.example.net", token="test")

    @patch(
        "pynetbox.core.query.requests.sessions.Session.get",
        return_value=MockedResponse(fixture="netbox/tests/fixtures/devices.json"),
    )
    def test_get_devices(self, *_):
        devices = self.netbox.get_devices()

        self.assertEqual(2, len(devices))
        self.assertEqual("router02.example.net", devices.pop().name)
        self.assertEqual("router01.example.net", devices.pop().name)

    @patch(
        "pynetbox.core.endpoint.RODetailEndpoint.list",
        return_value={
            "get_facts": MockedResponse(
                fixture="netbox/tests/fixtures/device_facts.json"
            ).json()
        },
    )
    def test_napalm(self, *_):
        with patch(
            "pynetbox.core.query.requests.sessions.Session.get",
            return_value=MockedResponse(fixture="netbox/tests/fixtures/device.json"),
        ):
            facts = self.netbox.napalm(1, "get_facts")
            self.assertEqual("router01", facts["hostname"])
