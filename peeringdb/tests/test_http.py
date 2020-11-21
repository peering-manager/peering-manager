import ipaddress

from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from peeringdb.http import PeeringDB
from peeringdb.models import Network, NetworkIXLAN
from utils.testing import MockedResponse


def mocked_get_autonomous_system(*args, **kwargs):
    if "asn" in kwargs["params"]:
        return MockedResponse(
            fixture="peeringdb/tests/fixtures/netixlans_as{}.json".format(
                kwargs["params"]["asn"]
            )
        )

    return MockedResponse(status_code=500)


def mocked_synchronization(*args, **kwargs):
    namespace = args[0].split("/")[-1]
    if namespace in ["ixpfx", "net", "netixlan", "poc"]:
        return MockedResponse(
            fixture="peeringdb/tests/fixtures/sync_{}.json".format(namespace)
        )

    return MockedResponse(status_code=500)


class PeeringDBHTTPTestCase(TestCase):
    def test_get_last_synchronization(self):
        api = PeeringDB()

        # Test when no sync has been done
        self.assertIsNone(api.get_last_synchronization())

        # Test of sync record with no objects
        time_of_sync = timezone.now()
        api.record_last_sync(time_of_sync, {"added": 0, "updated": 0, "deleted": 0})
        self.assertEqual(api.get_last_sync_time(), 0)

        # Test of sync record with one object
        time_of_sync = timezone.now()
        api.record_last_sync(time_of_sync, {"added": 1, "updated": 0, "deleted": 0})
        self.assertEqual(
            int(api.get_last_synchronization().time.timestamp()),
            int(time_of_sync.timestamp()),
        )

    def test_time_last_sync(self):
        api = PeeringDB()

        # Test when no sync has been done
        self.assertEqual(api.get_last_sync_time(), 0)

        # Test of sync record with no objects
        time_of_sync = timezone.now()
        api.record_last_sync(time_of_sync, {"added": 0, "updated": 0, "deleted": 0})
        self.assertEqual(api.get_last_sync_time(), 0)

        # Test of sync record with one object
        time_of_sync = timezone.now()
        api.record_last_sync(time_of_sync, {"added": 1, "updated": 0, "deleted": 0})
        self.assertEqual(api.get_last_sync_time(), int(time_of_sync.timestamp()))

    @patch("peeringdb.http.requests.get", side_effect=mocked_synchronization)
    def test_update_local_database(self, *_):
        sync_result = PeeringDB().update_local_database(0)
        self.assertEqual(8, sync_result.added)
        self.assertEqual(0, sync_result.updated)
        self.assertEqual(0, sync_result.deleted)

    def test_clear_local_database(self):
        try:
            PeeringDB().clear_local_database()
        except Exception:
            self.fail("Unexpected exception raised.")

    @patch(
        "peeringdb.http.requests.get",
        return_value=MockedResponse(fixture="peeringdb/tests/fixtures/as65536.json"),
    )
    def test_get_autonomous_system(self, *_):
        api = PeeringDB()
        asn = 65536

        # Must not exist
        with patch(
            "peeringdb.http.requests.get", return_value=MockedResponse(status_code=404)
        ):
            self.assertIsNone(api.get_autonomous_system(64500))

        # Using an API call (no cached data)
        autonomous_system = api.get_autonomous_system(asn)
        self.assertEqual(autonomous_system.asn, asn)

        # Save the data inside the cache
        details = {
            "id": autonomous_system.id,
            "asn": autonomous_system.asn,
            "name": autonomous_system.name,
        }
        network = Network(**details)
        network.save()

        # Using no API calls (cached data)
        autonomous_system = api.get_autonomous_system(asn)
        self.assertEqual(autonomous_system.asn, asn)

    @patch(
        "peeringdb.http.requests.get",
        return_value=MockedResponse(fixture="peeringdb/tests/fixtures/netixlan.json"),
    )
    def test_get_ix_network(self, *_):
        api = PeeringDB()
        ix_network_id = 1

        with patch(
            "peeringdb.http.requests.get", return_value=MockedResponse(status_code=404)
        ):
            # Must not exist
            self.assertIsNone(api.get_ix_network(0))

        # Using an API call (no cached data)
        ix_network = api.get_ix_network(ix_network_id)
        self.assertEqual(ix_network.id, ix_network_id)

        # Save the data inside the cache
        details = {
            "id": ix_network.id,
            "asn": ix_network.asn,
            "name": ix_network.name,
            "ix_id": ix_network.ix_id,
            "ixlan_id": ix_network.ixlan_id,
        }
        network_ixlan = NetworkIXLAN(**details)
        network_ixlan.save()

        # Using no API calls (cached data)
        ix_network = api.get_ix_network(ix_network_id)
        self.assertEqual(ix_network.id, ix_network_id)

    @patch(
        "peeringdb.http.requests.get",
        return_value=MockedResponse(fixture="peeringdb/tests/fixtures/netixlan.json"),
    )
    def test_get_ix_network_by_ip_address(self, *_):
        api = PeeringDB()
        ipv6_address = "2001:db8:1337::1"
        ipv4_address = "203.0.113.1"
        ix_network_id = 1

        # No IP given we cannot guess what the user wants
        self.assertIsNone(api.get_ix_network_by_ip_address())

        # Using an API call (no cached data)
        ix_network = api.get_ix_network_by_ip_address(ipv6_address=ipv6_address)
        self.assertEqual(ix_network.id, ix_network_id)
        ix_network = api.get_ix_network_by_ip_address(ipv4_address=ipv4_address)
        self.assertEqual(ix_network.id, ix_network_id)
        ix_network = api.get_ix_network_by_ip_address(
            ipv6_address=ipv6_address, ipv4_address=ipv4_address
        )
        self.assertEqual(ix_network.id, ix_network_id)

        # Save the data inside the cache
        details = {
            "id": ix_network.id,
            "asn": ix_network.asn,
            "name": ix_network.name,
            "ipaddr6": ipv6_address,
            "ipaddr4": ipv4_address,
            "ix_id": ix_network.ix_id,
            "ixlan_id": ix_network.ixlan_id,
        }
        network_ixlan = NetworkIXLAN(**details)
        network_ixlan.save()

        # Using no API calls (cached data)
        ix_network = api.get_ix_network_by_ip_address(ipv6_address=ipv6_address)
        self.assertEqual(ix_network.id, ix_network_id)
        ix_network = api.get_ix_network_by_ip_address(ipv4_address=ipv4_address)
        self.assertEqual(ix_network.id, ix_network_id)
        ix_network = api.get_ix_network_by_ip_address(
            ipv6_address=ipv6_address, ipv4_address=ipv4_address
        )
        self.assertEqual(ix_network.id, ix_network_id)

    @patch(
        "peeringdb.http.requests.get",
        return_value=MockedResponse(
            fixture="peeringdb/tests/fixtures/netixlans_as65536.json"
        ),
    )
    def test_get_ix_networks_for_asn(self, *_):
        api = PeeringDB()
        asn = 65536

        with patch(
            "peeringdb.http.requests.get", return_value=MockedResponse(status_code=404)
        ):
            # Must not exist
            self.assertIsNone(api.get_ix_networks_for_asn(64500))

        known_ix_networks = [1, 2]
        found_ix_networks = []

        ix_networks = api.get_ix_networks_for_asn(asn)
        for ix_network in ix_networks:
            found_ix_networks.append(ix_network.id)

        self.assertEqual(sorted(found_ix_networks), sorted(known_ix_networks))

    @patch("peeringdb.http.requests.get", side_effect=mocked_get_autonomous_system)
    def test_get_common_ix_networks_for_asns(self, *_):
        api = PeeringDB()
        asn1 = 65536
        asn2 = 65537

        with patch(
            "peeringdb.http.requests.get", return_value=MockedResponse(status_code=404)
        ):
            # Empty list should be returned
            self.assertFalse(api.get_common_ix_networks_for_asns(asn1, 64500))

        # Found common IX networks
        found_ix_networks = []
        for n1, n2 in api.get_common_ix_networks_for_asns(asn1, asn2):
            self.assertEqual(n1.ixlan_id, n2.ixlan_id)
            found_ix_networks.append(n1.ixlan_id)

        self.assertEqual([1], found_ix_networks)

    @patch(
        "peeringdb.http.requests.get",
        return_value=MockedResponse(fixture="peeringdb/tests/fixtures/ixpfx.json"),
    )
    def test_get_prefixes_for_ix_network(self, *_):
        api = PeeringDB()
        ix_network_id = 29146

        with patch(
            "peeringdb.http.requests.get", return_value=MockedResponse(status_code=404)
        ):
            # Must be empty
            self.assertFalse(api.get_prefixes_for_ix_network(0))

        known_prefixes = [
            ipaddress.ip_network("2001:db8:1337::/64"),
            ipaddress.ip_network("203.0.113.0/24"),
        ]
        found_prefixes = []

        for ix_prefix in api.get_prefixes_for_ix_network(ix_network_id):
            self.assertIn(ix_prefix, known_prefixes)
