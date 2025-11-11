from datetime import datetime

import pytz

from utils.testing import ViewTestCases

from ..models import (
    HiddenPeer,
    InternetExchange,
    IXLan,
    Network,
    NetworkIXLan,
    Organization,
)


class AutonomousSystemTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = HiddenPeer

    test_bulk_edit_objects = None

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

        HiddenPeer.objects.bulk_create(
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

        cls.form_data = {
            "peeringdb_network": cls.networks[0].pk,
            "peeringdb_ixlan": cls.ixlans[1].pk,
            "comments": "Bad peer",
        }
