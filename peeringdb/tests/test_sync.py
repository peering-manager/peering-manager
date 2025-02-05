from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from utils.testing import MockedResponse

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
