from django.utils import timezone

from peeringdb.filters import PeerRecordFilterSet, SynchronizationFilterSet
from peeringdb.models import Network, NetworkIXLAN, PeerRecord, Synchronization
from utils.testing import StandardTestCases


class PeerRecordTestCase(StandardTestCases.Filters):
    model = PeerRecord
    filter = PeerRecordFilterSet

    @classmethod
    def setUpTestData(cls):
        Network.objects.bulk_create(
            [
                Network(asn=64501, name="Test 1", irr_as_set="AS-TEST-1"),
                Network(asn=64502, name="Test 2", irr_as_set="AS-TEST-2"),
                Network(asn=64503, name="Test 3", irr_as_set="AS-TEST-3"),
            ]
        )
        NetworkIXLAN.objects.bulk_create(
            [
                NetworkIXLAN(
                    asn=64501,
                    name="Test 1",
                    ipaddr6="2001:db8::1",
                    ipaddr4="192.0.2.1",
                    ix_id=1,
                    ixlan_id=1,
                ),
                NetworkIXLAN(
                    asn=64502,
                    name="Test 2",
                    ipaddr6="2001:db8::2",
                    ipaddr4="192.0.2.2",
                    ix_id=1,
                    ixlan_id=1,
                ),
                NetworkIXLAN(
                    asn=64503,
                    name="Test 3",
                    ipaddr6="2001:db8::3",
                    ipaddr4="192.0.2.3",
                    ix_id=1,
                    ixlan_id=1,
                ),
            ]
        )
        PeerRecord.objects.bulk_create(
            [
                PeerRecord(
                    network=Network.objects.get(asn=64501),
                    network_ixlan=NetworkIXLAN.objects.get(asn=64501),
                ),
                PeerRecord(
                    network=Network.objects.get(asn=64502),
                    network_ixlan=NetworkIXLAN.objects.get(asn=64502),
                ),
                PeerRecord(
                    network=Network.objects.get(asn=64502),
                    network_ixlan=NetworkIXLAN.objects.get(asn=64503),
                ),
            ]
        )

    def test_q(self):
        params = {"q": "Test"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 3)
        params = {"q": "Test 1"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)
        params = {"q": "AS-TEST"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 3)
        params = {"q": "AS-TEST-1"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)
        params = {"q": "2001:db8::1"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)
        params = {"q": "192.0.2.1"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)
        params = {"q": 64501}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)

    def test_network__asn(self):
        params = {"network__asn": 64501}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)

    def test_network__asn(self):
        params = {"network__name": "Test 1"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)

    def test_network__asn(self):
        params = {"network__irr_as_set": "AS-TEST-1"}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)

    def test_network__info_prefixes6(self):
        params = {"network__info_prefixes6": 0}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 3)
        params = {"network__info_prefixes6": 1}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 0)

    def test_network__info_prefixes4(self):
        params = {"network__info_prefixes4": 0}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 3)
        params = {"network__info_prefixes4": 1}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 0)

    def test_visible(self):
        params = {"visible": True}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 3)
        params = {"visible": False}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 0)


class SynchronizationTestCase(StandardTestCases.Filters):
    model = Synchronization
    filter = SynchronizationFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.times = [timezone.now(), timezone.now(), timezone.now()]
        Synchronization.objects.bulk_create(
            [
                Synchronization(time=cls.times[0], added=1, updated=0, deleted=0),
                Synchronization(time=cls.times[1], added=0, updated=1, deleted=0),
                Synchronization(time=cls.times[2], added=0, updated=0, deleted=1),
            ]
        )

    def test_time(self):
        params = {"time": self.times[0]}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)

    def test_added(self):
        params = {"added": 1}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)
        params = {"added": 0}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 2)

    def test_updated(self):
        params = {"updated": 1}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)
        params = {"updated": 0}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 2)

    def test_deleted(self):
        params = {"deleted": 1}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 1)
        params = {"deleted": 0}
        self.assertEqual(self.filter(params, self.queryset).qs.count(), 2)
