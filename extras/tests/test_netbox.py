from unittest.mock import patch

import pynetbox
from django.test import TestCase

from utils.testing import MockedResponse

from ..netbox import NetBox


class MockedGenerator:
    def __init__(self, data):
        self._data = data

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __next__(self):
        return self._data


class NetBoxTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.netbox = NetBox()
        self.netbox.api = pynetbox.api("http://netbox.example.net", token="test")

    @patch(
        "requests.sessions.Session.get",
        return_value=MockedResponse(
            fixture="extras/tests/fixtures/netbox/devices.json"
        ),
    )
    def test_get_devices(self, *_):
        devices = self.netbox.get_devices()

        self.assertEqual(2, len(devices))
        self.assertEqual("router01.example.net", next(devices).name)
        self.assertEqual("router02.example.net", next(devices).name)
