from datetime import datetime

import pytz
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from utils.testing import APITestCase
from utils.testing.api import APIViewTestCases

from ..models import *
from ..sync import NAMESPACES


class CacheTest(APITestCase):
    def test_statistics(self):
        url = reverse("peeringdb-api:cache-statistics")
        response = self.client.get(url, **self.header)
        for namespace in [*list(NAMESPACES.keys()), "sync"]:
            self.assertEqual(response.data[f"{namespace}-count"], 0)

    def test_update_local(self):
        url = reverse("peeringdb-api:cache-update-local")
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)

    def test_clear_local(self):
        url = reverse("peeringdb-api:cache-clear-local")
        response = self.client.post(url, **self.header)
        self.assertEqual(response.data["status"], "success")


class SynchronisationTest(APITestCase):
    def setUp(self):
        super().setUp()

        for i in range(1, 10):
            Synchronisation.objects.create(
                time=timezone.now(), created=i, updated=i, deleted=i
            )

    def test_get_synchronisation(self):
        url = reverse("peeringdb-api:synchronisation-detail", kwargs={"pk": 1})
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["created"], 1)

    def test_list_synchronisations(self):
        url = reverse("peeringdb-api:synchronisation-list")
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data["count"], 9)


class HiddenPeerTest(APIViewTestCases.View):
    model = HiddenPeer
    brief_fields = [
        "id",
        "url",
        "display_url",
        "display",
        "peeringdb_network",
        "peeringdb_ixlan",
        "until",
    ]
    bulk_update_data = {"comments": "Bad peer"}

    @classmethod
    def setUpTestData(cls):
        cls.names = ["The Avengers", "S.H.I.E.L.D.", "Stark Industries"]
        cls.organisations = Organization.objects.bulk_create(
            [
                Organization(name=cls.names[0]),
                Organization(name=cls.names[1]),
                Organization(name=cls.names[2]),
            ]
        )
        cls.ixps = InternetExchange.objects.bulk_create(
            [
                InternetExchange(name=cls.names[0], org=cls.organisations[0]),
                InternetExchange(name=cls.names[1], org=cls.organisations[1]),
                InternetExchange(name=cls.names[2], org=cls.organisations[2]),
            ]
        )
        cls.ixlans = IXLan.objects.bulk_create(
            [
                IXLan(name=cls.names[0], rs_asn=64501, ix=cls.ixps[0], vlan=100),
                IXLan(name=cls.names[1], rs_asn=64502, ix=cls.ixps[1], vlan=200),
                IXLan(name=cls.names[2], rs_asn=64503, ix=cls.ixps[2], vlan=300),
            ]
        )
        cls.asns = [64500, 64496, 64498]
        cls.networks = Network.objects.bulk_create(
            [
                Network(asn=cls.asns[0], name=cls.names[0], org=cls.organisations[0]),
                Network(asn=cls.asns[1], name=cls.names[1], org=cls.organisations[1]),
                Network(asn=cls.asns[2], name=cls.names[2], org=cls.organisations[2]),
            ]
        )

        cls.netixlans = NetworkIXLan.objects.bulk_create(
            [
                NetworkIXLan(
                    net=cls.networks[0],
                    ixlan=cls.ixlans[0],
                    asn=cls.asns[0],
                    ipaddr6="2001:db8:100::1/64",
                    speed=1000,
                ),
                NetworkIXLan(
                    net=cls.networks[1],
                    ixlan=cls.ixlans[1],
                    asn=cls.asns[1],
                    ipaddr6="2001:db8:200::1/64",
                    speed=1000,
                ),
                NetworkIXLan(
                    net=cls.networks[2],
                    ixlan=cls.ixlans[2],
                    asn=cls.asns[2],
                    ipaddr6="2001:db8:300::1/64",
                    speed=1000,
                    is_rs_peer=True,
                ),
            ]
        )

        cls.hidden_peers = HiddenPeer.objects.bulk_create(
            [
                HiddenPeer(
                    peeringdb_network=cls.networks[0],
                    peeringdb_ixlan=cls.ixlans[0],
                    comments="Foo",
                ),
                HiddenPeer(
                    peeringdb_network=cls.networks[1],
                    peeringdb_ixlan=cls.ixlans[0],
                    until=str(datetime(2025, 1, 1, 0, 0, tzinfo=pytz.UTC)),
                    comments="Bar",
                ),
                HiddenPeer(
                    peeringdb_network=cls.networks[2], peeringdb_ixlan=cls.ixlans[0]
                ),
            ]
        )

        cls.create_data = [
            {
                "peeringdb_network": cls.networks[0].pk,
                "peeringdb_ixlan": cls.ixlans[1].pk,
            },
            {
                "peeringdb_network": cls.networks[1].pk,
                "peeringdb_ixlan": cls.ixlans[1].pk,
            },
            {
                "peeringdb_network": cls.networks[2].pk,
                "peeringdb_ixlan": cls.ixlans[1].pk,
            },
        ]
