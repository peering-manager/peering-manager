from django.test import TestCase

from bgp.models import Relationship
from devices.models import Router
from net.models import Connection
from utils.testing import BaseFilterSetTests

from ..constants import *
from ..enums import *
from ..filtersets import (
    AutonomousSystemFilterSet,
    BGPGroupFilterSet,
    CommunityFilterSet,
    DirectPeeringSessionFilterSet,
    InternetExchangeFilterSet,
    InternetExchangePeeringSessionFilterSet,
    RoutingPolicyFilterSet,
)
from ..models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)


class AutonomousSystemTestCase(TestCase, BaseFilterSetTests):
    queryset = AutonomousSystem.objects.all()
    filterset = AutonomousSystemFilterSet

    @classmethod
    def setUpTestData(cls):
        AutonomousSystem.objects.bulk_create(
            [
                AutonomousSystem(
                    asn=64501,
                    name="Autonomous System 1",
                    irr_as_set="AS-SET-1",
                    ipv6_max_prefixes=1,
                    ipv4_max_prefixes=0,
                    affiliated=True,
                ),
                AutonomousSystem(
                    asn=64502,
                    name="Autonomous System 2",
                    irr_as_set="AS-SET-2",
                    ipv6_max_prefixes=0,
                    ipv4_max_prefixes=1,
                ),
                AutonomousSystem(
                    asn=64503,
                    name="Autonomous System 3",
                    irr_as_set="AS-SET-3",
                    ipv6_max_prefixes=0,
                    ipv4_max_prefixes=0,
                ),
            ]
        )

    def test_q(self):
        params = {"q": "Autonomous System 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "AS-SET-1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_asn(self):
        params = {"asn": [64501]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"asn": [64501, 64502]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_ipv6_max_prefixes(self):
        params = {"ipv6_max_prefixes": [1]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"ipv6_max_prefixes": [0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"ipv6_max_prefixes": [0, 1]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_ipv4_max_prefixes(self):
        params = {"ipv4_max_prefixes": [1]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"ipv4_max_prefixes": [0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"ipv4_max_prefixes": [0, 1]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_affiliated(self):
        params = {"affiliated": False}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"affiliated": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class BGPGroupTestCase(TestCase, BaseFilterSetTests):
    queryset = BGPGroup.objects.all()
    filterset = BGPGroupFilterSet

    @classmethod
    def setUpTestData(cls):
        BGPGroup.objects.bulk_create(
            [
                BGPGroup(name="BGP Group 1", slug="bgp-group-1"),
                BGPGroup(name="BGP Group 2", slug="bgp-group-2"),
                BGPGroup(
                    name="BGP Group 3",
                    slug="bgp-group-3",
                    status=BGPGroupStatus.DISABLED,
                ),
            ]
        )

    def test_q(self):
        params = {"q": "BGP Group 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "bgp-group-1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_status(self):
        params = {"status": [BGPGroupStatus.ENABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"status": [BGPGroupStatus.DISABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"status": [BGPGroupStatus.ENABLED, BGPGroupStatus.DISABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)


class CommunityTestCase(TestCase, BaseFilterSetTests):
    queryset = Community.objects.all()
    filterset = CommunityFilterSet

    @classmethod
    def setUpTestData(cls):
        Community.objects.bulk_create(
            [
                Community(
                    name="Community 1",
                    slug="community-1",
                    value="64500:1",
                    type=CommunityType.EGRESS,
                ),
                Community(
                    name="Community 2",
                    slug="community-2",
                    value="64500:2",
                    type=CommunityType.INGRESS,
                ),
                Community(name="Community 3", slug="community-3", value="64500:3"),
            ]
        )

    def test_q(self):
        params = {"q": "Community 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "community-1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_type(self):
        params = {"type": [""]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"type": [CommunityType.INGRESS]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"type": [CommunityType.EGRESS]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_value(self):
        params = {"value": ["64500:1"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class DirectPeeringSessionTestCase(TestCase, BaseFilterSetTests):
    queryset = DirectPeeringSession.objects.all()
    filterset = DirectPeeringSessionFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.local_as = AutonomousSystem.objects.create(
            asn=64501, name="Autonomous System 1", affiliated=True
        )
        cls.a_s = AutonomousSystem.objects.create(asn=64502, name="Autonomous System 2")
        cls.router = Router.objects.create(
            name="Router 1",
            hostname="router1.example.net",
            local_autonomous_system=cls.local_as,
        )
        cls.relationship_transit = Relationship.objects.create(
            name="Transit", slug="transit"
        )
        relationship_private_peering = Relationship.objects.create(
            name="Private Peering", slug="private-peering"
        )
        relationship_customer = Relationship.objects.create(
            name="Customer", slug="customer"
        )
        DirectPeeringSession.objects.bulk_create(
            [
                DirectPeeringSession(
                    service_reference="TRANSIT-0001",
                    local_autonomous_system=cls.local_as,
                    autonomous_system=cls.a_s,
                    ip_address="192.0.2.1",
                    relationship=cls.relationship_transit,
                    router=cls.router,
                ),
                DirectPeeringSession(
                    local_autonomous_system=cls.local_as,
                    autonomous_system=cls.a_s,
                    ip_address="192.0.2.2",
                    relationship=relationship_private_peering,
                    multihop_ttl=2,
                ),
                DirectPeeringSession(
                    local_autonomous_system=cls.local_as,
                    autonomous_system=cls.a_s,
                    ip_address="192.0.2.3",
                    status=BGPSessionStatus.DISABLED,
                    relationship=relationship_customer,
                    passive=True,
                ),
            ]
        )

    def test_q(self):
        params = {"q": "TRANSIT-0001"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_address_family(self):
        params = {"address_family": 4}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"address_family": 6}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_relationship(self):
        params = {"relationship_id": [self.relationship_transit.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_router_id(self):
        params = {"router_id": [self.router.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_local_autonomous_system_id(self):
        params = {"local_autonomous_system_id": [self.local_as.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"local_autonomous_system_id": [self.a_s.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_autonomous_system_id(self):
        params = {"autonomous_system_id": [self.local_as.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
        params = {"autonomous_system_id": [self.a_s.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_multihop_ttl(self):
        params = {"multihop_ttl": [1]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"multihop_ttl": [2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_passive(self):
        params = {"passive": False}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"passive": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_status(self):
        params = {"status": [BGPSessionStatus.ENABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"status": [BGPSessionStatus.DISABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"status": [BGPSessionStatus.ENABLED, BGPSessionStatus.DISABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)


class InternetExchangeTestCase(TestCase, BaseFilterSetTests):
    queryset = InternetExchange.objects.all()
    filterset = InternetExchangeFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.local_as = AutonomousSystem.objects.create(
            asn=64501, name="Autonomous System 1", affiliated=True
        )
        InternetExchange.objects.bulk_create(
            [
                InternetExchange(name="Internet Exchange 1", slug="ix-1"),
                InternetExchange(name="Internet Exchange 2", slug="ix-2"),
                InternetExchange(
                    local_autonomous_system=cls.local_as,
                    name="Internet Exchange 3",
                    slug="ix-3",
                    status=BGPGroupStatus.DISABLED,
                ),
            ]
        )

    def test_q(self):
        params = {"q": "Internet Exchange 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "ix-1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_local_autonomous_system_id(self):
        params = {"local_autonomous_system_id": [self.local_as.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_status(self):
        params = {"status": [BGPGroupStatus.ENABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"status": [BGPGroupStatus.DISABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"status": [BGPGroupStatus.ENABLED, BGPGroupStatus.DISABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)


class InternetExchangePeeringSessionTestCase(TestCase, BaseFilterSetTests):
    queryset = InternetExchangePeeringSession.objects.all()
    filterset = InternetExchangePeeringSessionFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.local_as = AutonomousSystem.objects.create(
            asn=64500, name="Autonomous System 1", affiliated=True
        )
        cls.a_s = AutonomousSystem.objects.create(asn=64501, name="Autonomous System 1")
        cls.ixp = InternetExchange.objects.create(
            local_autonomous_system=cls.local_as,
            name="Internet Exchange 1",
            slug="ix-1",
        )
        cls.useless_ixp = InternetExchange.objects.create(
            local_autonomous_system=cls.local_as,
            name="Internet Exchange 2",
            slug="ix-2",
        )
        cls.ixp_connection = Connection.objects.create(
            vlan=2000, internet_exchange_point=cls.ixp
        )
        InternetExchangePeeringSession.objects.bulk_create(
            [
                InternetExchangePeeringSession(
                    service_reference="IXP-0001",
                    autonomous_system=cls.a_s,
                    ixp_connection=cls.ixp_connection,
                    ip_address="192.0.2.1",
                    multihop_ttl=2,
                ),
                InternetExchangePeeringSession(
                    autonomous_system=cls.a_s,
                    ixp_connection=cls.ixp_connection,
                    ip_address="192.0.2.2",
                    status=BGPSessionStatus.DISABLED,
                    passive=True,
                ),
                InternetExchangePeeringSession(
                    autonomous_system=cls.a_s,
                    ixp_connection=cls.ixp_connection,
                    ip_address="192.0.2.3",
                    is_route_server=True,
                ),
            ]
        )

    def test_q(self):
        params = {"q": "IXP-0001"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_address_family(self):
        params = {"address_family": 4}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"address_family": 6}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_multihop_ttl(self):
        params = {"multihop_ttl": [1]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"multihop_ttl": [2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_status(self):
        params = {"status": [BGPSessionStatus.ENABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"status": [BGPSessionStatus.DISABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"status": [BGPSessionStatus.ENABLED, BGPSessionStatus.DISABLED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_passive(self):
        params = {"passive": False}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"passive": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_is_route_server(self):
        params = {"is_route_server": False}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"is_route_server": True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_autonomous_system_asn(self):
        params = {"autonomous_system_asn": [self.a_s.asn]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"autonomous_system_asn": [self.local_as.asn]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_autonomous_system_id(self):
        params = {"autonomous_system_id": [self.a_s.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"autonomous_system_id": [self.local_as.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_autonomous_system(self):
        params = {"autonomous_system": [self.a_s.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"autonomous_system": [self.local_as.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_internet_exchange_id(self):
        params = {"internet_exchange_id": [self.ixp.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"internet_exchange_id": [self.useless_ixp.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_internet_exchange(self):
        params = {"internet_exchange": [self.ixp.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {"internet_exchange": [self.useless_ixp.name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_connection_id(self):
        params = {"connection_id": [self.ixp_connection.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)


class RoutingPolicyTestCase(TestCase, BaseFilterSetTests):
    queryset = RoutingPolicy.objects.all()
    filterset = RoutingPolicyFilterSet

    @classmethod
    def setUpTestData(cls):
        RoutingPolicy.objects.bulk_create(
            [
                RoutingPolicy(
                    name="Routing Policy 1",
                    slug="routing-policy-1",
                    type=RoutingPolicyType.EXPORT,
                    weight=0,
                ),
                RoutingPolicy(
                    name="Routing Policy 2",
                    slug="routing-policy-2",
                    type=RoutingPolicyType.IMPORT,
                    weight=0,
                    address_family=6,
                ),
                RoutingPolicy(
                    name="Routing Policy 3",
                    slug="routing-policy-3",
                    type=RoutingPolicyType.IMPORT_EXPORT,
                    weight=10,
                ),
            ]
        )

    def test_q(self):
        params = {"q": "Routing Policy 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"q": "routing-policy-1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_type(self):
        params = {"type": [RoutingPolicyType.IMPORT]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"type": [RoutingPolicyType.EXPORT]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"type": [RoutingPolicyType.IMPORT_EXPORT]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_weight(self):
        params = {"weight": [0]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {"weight": [10]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_address_family(self):
        params = {"address_family": 6}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"address_family": 4}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
