from datetime import datetime

import pytz
from django.test import TestCase
from django.utils import timezone

from ..enums import *
from ..filtersets import *
from ..models import *


class InternetExchangeTestCase(TestCase):
    queryset = InternetExchange.objects.all()
    filterset = InternetExchangeFilterSet

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

    def test_q(self):
        self.assertEqual(self.filterset({"q": "stark"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "unknown"}, self.queryset).qs.count(), 0)

    def test_name(self):
        for name in self.names:
            self.assertEqual(
                self.filterset({"name": name}, self.queryset).qs.count(), 1
            )
        self.assertEqual(
            self.filterset({"name": "Unknown"}, self.queryset).qs.count(), 0
        )

    def test_org_id(self):
        params = {"org_id": [self.organisations[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"org_id": [self.organisations[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"org_id": [self.organisations[2].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class InternetExchangeFacilityTestCase(TestCase):
    queryset = InternetExchangeFacility.objects.all()
    filterset = InternetExchangeFacilityFilterSet

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

        cls.fac_names = ["Avengers Campus", "Stark Industries"]
        cls.facilities = Facility.objects.bulk_create(
            [
                Facility(name=cls.fac_names[0], org=cls.organisations[0]),
                Facility(name=cls.fac_names[1], org=cls.organisations[2]),
            ]
        )

        cls.ixp_facilities = InternetExchangeFacility.objects.bulk_create(
            [
                InternetExchangeFacility(ix=cls.ixps[0], fac=cls.facilities[0]),
                InternetExchangeFacility(ix=cls.ixps[1], fac=cls.facilities[0]),
                InternetExchangeFacility(ix=cls.ixps[2], fac=cls.facilities[0]),
                InternetExchangeFacility(ix=cls.ixps[2], fac=cls.facilities[1]),
            ]
        )

    def test_fac_id(self):
        params = {"fac_id": [self.facilities[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"fac_id": [self.facilities[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_ix_id(self):
        params = {"ix_id": [self.ixps[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"ix_id": [self.ixps[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"ix_id": [self.ixps[2].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class FacilityTestCase(TestCase):
    queryset = Facility.objects.all()
    filterset = FacilityFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.org_names = ["The Avengers", "S.H.I.E.L.D.", "Stark Industries"]
        cls.organisations = Organization.objects.bulk_create(
            [
                Organization(name=cls.org_names[0]),
                Organization(name=cls.org_names[1]),
                Organization(name=cls.org_names[2]),
            ]
        )

        cls.names = ["Avengers Campus", "Stark Industries"]
        cls.facilities = Facility.objects.bulk_create(
            [
                Facility(name=cls.names[0], org=cls.organisations[0]),
                Facility(name=cls.names[1], org=cls.organisations[2]),
            ]
        )

    def test_q(self):
        self.assertEqual(self.filterset({"q": "stark"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "unknown"}, self.queryset).qs.count(), 0)

    def test_name(self):
        for name in self.names:
            self.assertEqual(
                self.filterset({"name": name}, self.queryset).qs.count(), 1
            )
        self.assertEqual(
            self.filterset({"name": "Unknown"}, self.queryset).qs.count(), 0
        )

    def test_org_id(self):
        params = {"org_id": [self.organisations[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"org_id": [self.organisations[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
        params = {"org_id": [self.organisations[2].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class IXLanTestCase(TestCase):
    queryset = IXLan.objects.all()
    filterset = IXLanFilterSet

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

    def test_rs_asn(self):
        params = {"rs_asn": 64501}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"rs_asn": 64502}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"rs_asn": 64503}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"rs_asn": 64504}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_vlan(self):
        params = {"vlan": 100}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"vlan": 200}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"vlan": 300}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"vlan": 400}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_ix_id(self):
        params = {"ix_id": [self.ixps[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"ix_id": [self.ixps[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"ix_id": [self.ixps[2].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class IXLanPrefixTestCase(TestCase):
    queryset = IXLanPrefix.objects.all()
    filterset = IXLanPrefixFilterSet

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
        cls.ixlanpfxs = IXLanPrefix.objects.bulk_create(
            [
                IXLanPrefix(
                    prefix="2001:db8:100::/64",
                    protocol=Protocol.IPV6,
                    ixlan=cls.ixlans[0],
                ),
                IXLanPrefix(
                    prefix="2001:db8:200::/64",
                    protocol=Protocol.IPV6,
                    ixlan=cls.ixlans[1],
                ),
                IXLanPrefix(
                    prefix="2001:db8:300::/64",
                    protocol=Protocol.IPV6,
                    ixlan=cls.ixlans[2],
                    in_dfz=True,
                ),
            ]
        )

    def test_q(self):
        params = {"q": "2001:db8:100::/64"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "2001:db8:200::/64"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "2001:db8:300::/64"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "unknown"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_in_dfz(self):
        params = {"in_dfz": False}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"in_dfz": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_ixlan_id(self):
        params = {"ixlan_id": [self.ixlans[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"ixlan_id": [self.ixlans[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"ixlan_id": [self.ixlans[2].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class NetworkTestCase(TestCase):
    queryset = Network.objects.all()
    filterset = NetworkFilterSet

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

        cls.asns = [64500, 64496, 64498]
        cls.networks = Network.objects.bulk_create(
            [
                Network(asn=cls.asns[0], name=cls.names[0], org=cls.organisations[0]),
                Network(asn=cls.asns[1], name=cls.names[1], org=cls.organisations[1]),
                Network(asn=cls.asns[2], name=cls.names[2], org=cls.organisations[2]),
            ]
        )

    def test_q(self):
        self.assertEqual(self.filterset({"q": "stark"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "unknown"}, self.queryset).qs.count(), 0)

    def test_asn(self):
        for asn in self.asns:
            self.assertEqual(self.filterset({"asn": asn}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"asn": "64555"}, self.queryset).qs.count(), 0)

    def test_name(self):
        for name in self.names:
            self.assertEqual(
                self.filterset({"name": name}, self.queryset).qs.count(), 1
            )
        self.assertEqual(
            self.filterset({"name": "Unknown"}, self.queryset).qs.count(), 0
        )

    def test_org_id(self):
        params = {"org_id": [self.organisations[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"org_id": [self.organisations[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"org_id": [self.organisations[2].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class NetworkContactTestCase(TestCase):
    queryset = NetworkContact.objects.all()
    filterset = NetworkContactFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.org_names = ["The Avengers", "S.H.I.E.L.D.", "Stark Industries"]
        cls.organisations = Organization.objects.bulk_create(
            [
                Organization(name=cls.org_names[0]),
                Organization(name=cls.org_names[1]),
                Organization(name=cls.org_names[2]),
            ]
        )

        cls.asns = [64500, 64496, 64498]
        cls.networks = Network.objects.bulk_create(
            [
                Network(
                    asn=cls.asns[0], name=cls.org_names[0], org=cls.organisations[0]
                ),
                Network(
                    asn=cls.asns[1], name=cls.org_names[1], org=cls.organisations[1]
                ),
                Network(
                    asn=cls.asns[2], name=cls.org_names[2], org=cls.organisations[2]
                ),
            ]
        )

        cls.names = ["Tech Team", "Policy Team", "NOC Team"]
        cls.emails = ["avengers@example.com", "shield@example.com", "stark@example.com"]
        cls.contacts = NetworkContact.objects.bulk_create(
            [
                NetworkContact(
                    role=POCRole.TECHNICAL,
                    visible=Visibility.PUBLIC,
                    name=cls.names[0],
                    email=cls.emails[0],
                    net=cls.networks[0],
                ),
                NetworkContact(
                    role=POCRole.POLICY,
                    visible=Visibility.PUBLIC,
                    name=cls.names[1],
                    email=cls.emails[1],
                    net=cls.networks[1],
                ),
                NetworkContact(
                    role=POCRole.NOC,
                    visible=Visibility.PUBLIC,
                    name=cls.names[2],
                    email=cls.emails[2],
                    net=cls.networks[2],
                ),
            ]
        )

    def test_role(self):
        self.assertEqual(
            self.filterset({"role": POCRole.NOC}, self.queryset).qs.count(), 1
        )
        self.assertEqual(
            self.filterset({"role": POCRole.MAINTENANCE}, self.queryset).qs.count(), 0
        )

    def test_name(self):
        for name in self.names:
            self.assertEqual(
                self.filterset({"name": name}, self.queryset).qs.count(), 1
            )
        self.assertEqual(
            self.filterset({"name": "unknown"}, self.queryset).qs.count(), 0
        )

    def test_email(self):
        for email in self.emails:
            self.assertEqual(
                self.filterset({"email": email}, self.queryset).qs.count(), 1
            )
        self.assertEqual(
            self.filterset({"email": "unknown"}, self.queryset).qs.count(), 0
        )

    def test_net_id(self):
        params = {"net_id": [self.networks[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"net_id": [self.networks[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"net_id": [self.networks[2].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_net_asn(self):
        params = {"net_asn": [self.networks[0].asn]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"net_asn": [self.networks[1].asn]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"net_asn": [self.networks[2].asn]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class NetworkFacilityTestCase(TestCase):
    queryset = NetworkFacility.objects.all()
    filterset = NetworkFacilityFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.org_names = ["The Avengers", "S.H.I.E.L.D.", "Stark Industries"]
        cls.organisations = Organization.objects.bulk_create(
            [
                Organization(name=cls.org_names[0]),
                Organization(name=cls.org_names[1]),
                Organization(name=cls.org_names[2]),
            ]
        )

        cls.asns = [64500, 64496, 64498]
        cls.networks = Network.objects.bulk_create(
            [
                Network(
                    asn=cls.asns[0], name=cls.org_names[0], org=cls.organisations[0]
                ),
                Network(
                    asn=cls.asns[1], name=cls.org_names[1], org=cls.organisations[1]
                ),
                Network(
                    asn=cls.asns[2], name=cls.org_names[2], org=cls.organisations[2]
                ),
            ]
        )

        cls.fac_names = ["Avengers Campus", "Stark Industries"]
        cls.facilities = Facility.objects.bulk_create(
            [
                Facility(name=cls.fac_names[0], org=cls.organisations[0]),
                Facility(name=cls.fac_names[1], org=cls.organisations[2]),
            ]
        )

        cls.asns = [64500, 64496, 64498]
        cls.netfacilities = NetworkFacility.objects.bulk_create(
            [
                NetworkFacility(
                    net=cls.networks[0], fac=cls.facilities[0], local_asn=cls.asns[0]
                ),
                NetworkFacility(
                    net=cls.networks[1], fac=cls.facilities[0], local_asn=cls.asns[1]
                ),
                NetworkFacility(
                    net=cls.networks[2], fac=cls.facilities[1], local_asn=cls.asns[2]
                ),
            ]
        )

    def test_asn(self):
        for asn in self.asns:
            self.assertEqual(
                self.filterset({"local_asn": asn}, self.queryset).qs.count(), 1
            )
        self.assertEqual(
            self.filterset({"local_asn": "64555"}, self.queryset).qs.count(), 0
        )

    def test_net_id(self):
        params = {"net_id": [self.networks[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"net_id": [self.networks[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"net_id": [self.networks[2].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_fac_id(self):
        params = {"fac_id": [self.facilities[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"fac_id": [self.facilities[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class NetworkIXLanTestCase(TestCase):
    queryset = NetworkIXLan.objects.all()
    filterset = NetworkIXLanFilterSet

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

    def test_q(self):
        self.assertEqual(self.filterset({"q": "stark"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "64500"}, self.queryset).qs.count(), 1)
        self.assertEqual(
            self.filterset({"q": "2001:db8:100::1"}, self.queryset).qs.count(), 1
        )
        self.assertEqual(self.filterset({"q": "unknown"}, self.queryset).qs.count(), 0)

    def test_net_id(self):
        params = {"net_id": [self.networks[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"net_id": [self.networks[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"net_id": [self.networks[2].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_net_asn(self):
        params = {"net_asn": [self.asns[0]]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"net_asn": [self.asns[1]]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"net_asn": [self.asns[2]]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_ixlan_id(self):
        params = {"ixlan_id": [self.ixlans[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"ixlan_id": [self.ixlans[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"ixlan_id": [self.ixlans[2].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class OrganizationTestCase(TestCase):
    queryset = Organization.objects.all()
    filterset = OrganizationFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.names = ["The Avengers", "S.H.I.E.L.D.", "Stark Industries"]
        Organization.objects.bulk_create(
            [
                Organization(name=cls.names[0]),
                Organization(name=cls.names[1]),
                Organization(name=cls.names[2]),
            ]
        )

    def test_q(self):
        self.assertEqual(self.filterset({"q": "stark"}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({"q": "unknown"}, self.queryset).qs.count(), 0)

    def test_name(self):
        for name in self.names:
            self.assertEqual(
                self.filterset({"name": name}, self.queryset).qs.count(), 1
            )
        self.assertEqual(
            self.filterset({"name": "Unknown"}, self.queryset).qs.count(), 0
        )


class SynchronisationTestCase(TestCase):
    queryset = Synchronisation.objects.all()
    filterset = SynchronisationFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.times = [timezone.now(), timezone.now(), timezone.now()]
        Synchronisation.objects.bulk_create(
            [
                Synchronisation(time=cls.times[0], created=1, updated=0, deleted=0),
                Synchronisation(time=cls.times[1], created=0, updated=1, deleted=0),
                Synchronisation(time=cls.times[2], created=0, updated=0, deleted=1),
            ]
        )

    def test_time(self):
        params = {"time": self.times[0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_created(self):
        params = {"created": 1}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"created": 0}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_updated(self):
        params = {"updated": 1}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"updated": 0}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_deleted(self):
        params = {"deleted": 1}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"deleted": 0}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class HiddenPeerTestCase(TestCase):
    queryset = HiddenPeer.objects.all()
    filterset = HiddenPeerFilterSet

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
                    peeringdb_ixlan=cls.ixlans[1],
                    until=str(datetime(2025, 1, 1, 0, 0, tzinfo=pytz.UTC)),
                    comments="Bar",
                ),
            ]
        )

    def test_q(self):
        self.assertEqual(self.filterset({"q": "64500"}, self.queryset).qs.count(), 1)
        self.assertEqual(
            self.filterset({"q": "The Avengers"}, self.queryset).qs.count(), 1
        )
        self.assertEqual(self.filterset({"q": "unknown"}, self.queryset).qs.count(), 0)

    def test_peeringdb_network_id(self):
        params = {"peeringdb_network_id": [self.networks[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_peeringdb_network_asn(self):
        params = {"peeringdb_network_asn": [self.asns[0]]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_peeringdb_ixlan_id(self):
        params = {"peeringdb_ixlan_id": [self.ixlans[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_is_expired(self):
        params = {"is_expired": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"is_expired": False}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"is_expired": None}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
