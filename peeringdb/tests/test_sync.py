from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from utils.testing import MockedResponse

from ..models import HiddenPeer, InternetExchange, IXLan, Network, Organization
from ..sync import *


def mocked_synchronisation(*args, **kwargs):
    namespace = args[0].split("/")[-1]
    if namespace in NAMESPACES:
        return MockedResponse(fixture=f"peeringdb/tests/fixtures/{namespace}.json")

    return MockedResponse(status_code=500)


class PeeringDBSyncTestCase(TestCase):
    def test_get_last_synchronisation(self):
        api = PeeringDB()

        # Test when no sync has been done
        self.assertIsNone(api.get_last_synchronisation())

        # Test of sync record with no objects
        time_of_sync = timezone.now()
        api.record_last_sync(time_of_sync, {"created": 0, "updated": 0, "deleted": 0})
        self.assertIsNone(api.get_last_synchronisation())

        # Test of sync record with one object
        time_of_sync = timezone.now()
        api.record_last_sync(time_of_sync, {"created": 1, "updated": 0, "deleted": 0})
        self.assertEqual(
            int(api.get_last_synchronisation().time.timestamp()),
            int(time_of_sync.timestamp()),
        )

    @patch("peeringdb.sync.requests.get", side_effect=mocked_synchronisation)
    def test_update_local_database(self, *_):
        sync_result = PeeringDB().update_local_database()
        self.assertEqual(24, sync_result.created)
        self.assertEqual(0, sync_result.updated)
        self.assertEqual(0, sync_result.deleted)

    def test_clear_local_database(self):
        try:
            PeeringDB().clear_local_database()
        except Exception:
            self.fail("Unexpected exception raised.")


class HiddenPeerLinkTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(name="Foo")
        cls.network = Network.objects.create(asn=64500, name="Bar", org=cls.org)
        cls.ix = InternetExchange.objects.create(name="Baz", org=cls.org)
        cls.ixlan = IXLan.objects.create(ix=cls.ix)

    def test_hidden_peer_save_ids(self):
        hidden_peer = HiddenPeer.objects.create(
            peeringdb_network=self.network, peeringdb_ixlan=self.ixlan
        )

        self.assertEqual(hidden_peer.peeringdb_network_id_copy, self.network.pk)
        self.assertEqual(hidden_peer.peeringdb_ixlan_id_copy, self.ixlan.pk)

    def test_hidden_peer_link_to_peeringdb(self):
        hidden_peer = HiddenPeer.objects.create(
            peeringdb_network=self.network, peeringdb_ixlan=self.ixlan
        )

        # Simulate cache clear
        HiddenPeer.objects.filter(pk=hidden_peer.pk).update(
            peeringdb_network=None, peeringdb_ixlan=None
        )
        hidden_peer.refresh_from_db()

        self.assertIsNone(hidden_peer.peeringdb_network)
        self.assertIsNone(hidden_peer.peeringdb_ixlan)
        self.assertEqual(hidden_peer.peeringdb_network_id_copy, self.network.pk)
        self.assertEqual(hidden_peer.peeringdb_ixlan_id_copy, self.ixlan.pk)

        result = hidden_peer.link_to_peeringdb()

        self.assertTrue(result)
        self.assertEqual(hidden_peer.peeringdb_network, self.network)
        self.assertEqual(hidden_peer.peeringdb_ixlan, self.ixlan)

    def test_hidden_peer_link_to_peeringdb_partial_failure(self):
        hidden_peer = HiddenPeer.objects.create(
            peeringdb_network=self.network, peeringdb_ixlan=self.ixlan
        )

        HiddenPeer.objects.filter(pk=hidden_peer.pk).update(
            peeringdb_network=None, peeringdb_ixlan=None
        )
        hidden_peer.refresh_from_db()

        # Delete only the network from cache
        self.network.delete()

        result = hidden_peer.link_to_peeringdb()

        self.assertFalse(result)
        self.assertIsNone(hidden_peer.peeringdb_network)
        self.assertEqual(hidden_peer.peeringdb_ixlan, self.ixlan)
