from unittest.mock import patch

from django.urls import reverse
from rest_framework import status

from devices.models import Platform
from net.models import Connection
from peering.constants import *
from peering.enums import BGPRelationship, CommunityType, DeviceState, RoutingPolicyType
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    Configuration,
    DirectPeeringSession,
    Email,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from peering.tests.mocked_data import load_peeringdb_data, mocked_subprocess_popen
from utils.testing import APITestCase, StandardAPITestCases


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("peering-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class StaticChoiceTest(APITestCase):
    def test_list_static_choices(self):
        url = reverse("peering-api:field-choice-list")
        response = self.client.get(url, **self.header)
        self.assertEqual(len(response.data), 6)


class AutonomousSystemTest(StandardAPITestCases.View):
    model = AutonomousSystem
    brief_fields = [
        "id",
        "url",
        "display",
        "asn",
        "name",
        "ipv6_max_prefixes",
        "ipv4_max_prefixes",
    ]
    create_data = [
        {"asn": 64541, "name": "Test 1"},
        {"asn": 64542, "name": "Test 2"},
        {"asn": 64543, "name": "Test 3"},
    ]
    bulk_update_data = {"comments": "Awesome peer"}

    @classmethod
    def setUpTestData(cls):
        AutonomousSystem.objects.bulk_create(
            [
                AutonomousSystem(asn=65536, name="Example 1", irr_as_set="AS-MOCKED"),
                AutonomousSystem(
                    asn=64496, name="Example 2", irr_as_set="AS-EXAMPLE-2"
                ),
                AutonomousSystem(
                    asn=64497, name="Example 3", irr_as_set="AS-EXAMPLE-3"
                ),
            ]
        )
        cls.autonomous_system = AutonomousSystem.objects.get(asn=65536)
        load_peeringdb_data()

    def test_synchronize_with_peeringdb(self):
        autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Test", irr_as_set="AS-TEST"
        )
        url = reverse(
            "peering-api:autonomoussystem-synchronize-with-peeringdb",
            kwargs={"pk": autonomous_system.pk},
        )
        response = self.client.post(url, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)

    def test_get_irr_as_set_prefixes(self):
        with patch("peering.subprocess.Popen", side_effect=mocked_subprocess_popen):
            url = reverse(
                "peering-api:autonomoussystem-get-irr-as-set-prefixes",
                kwargs={"pk": self.autonomous_system.pk},
            )
            response = self.client.get(url, format="json", **self.header)
            self.assertHttpStatus(response, status.HTTP_200_OK)
            self.assertEqual(len(response.data["prefixes"]["ipv6"]), 1)
            self.assertEqual(len(response.data["prefixes"]["ipv4"]), 1)

    def test_shared_internet_exchanges(self):
        local_as = AutonomousSystem.objects.create(
            asn=65535, name="Local", irr_as_set="AS-LOCAL", affiliated=True
        )
        self.user.preferences.set("context.as", local_as.pk, commit=True)
        url = reverse(
            "peering-api:autonomoussystem-shared-internet-exchanges",
            kwargs={"pk": self.autonomous_system.pk},
        )
        response = self.client.get(url, format="json", **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data["shared-internet-exchanges"], [])


class BGPGroupTest(StandardAPITestCases.View):
    model = BGPGroup
    brief_fields = ["id", "url", "display", "name", "slug"]
    create_data = [
        {"name": "Test 1", "slug": "test-1"},
        {"name": "Test 2", "slug": "test-2"},
        {"name": "Test 3", "slug": "test-3"},
    ]
    bulk_update_data = {"comments": "Awesome group"}

    @classmethod
    def setUpTestData(cls):
        BGPGroup.objects.bulk_create(
            [
                BGPGroup(name="Example 1", slug="example-1"),
                BGPGroup(name="Example 2", slug="example-2"),
                BGPGroup(name="Example 3", slug="example-3"),
            ]
        )

    def test_poll_peering_sessions(self):
        url = reverse(
            "peering-api:bgpgroup-poll-peering-sessions",
            kwargs={"pk": BGPGroup.objects.get(slug="example-1").pk},
        )
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)


class CommunityTest(StandardAPITestCases.View):
    model = Community
    brief_fields = ["id", "url", "display", "name", "slug", "value", "type"]
    create_data = [
        {
            "name": "Test1",
            "slug": "test1",
            "value": "64500:11",
            "type": CommunityType.EGRESS,
        },
        {
            "name": "Test2",
            "slug": "test2",
            "value": "64500:12",
            "type": CommunityType.EGRESS,
        },
        {
            "name": "Test3",
            "slug": "test3",
            "value": "64500:13",
            "type": CommunityType.EGRESS,
        },
    ]
    bulk_update_data = {"comments": "Awesome community"}

    @classmethod
    def setUpTestData(cls):
        Community.objects.bulk_create(
            [
                Community(
                    name="Example 1",
                    slug="example-1",
                    value="64500:1",
                    type=CommunityType.EGRESS,
                ),
                Community(
                    name="Example 2",
                    slug="example-2",
                    value="64500:2",
                    type=CommunityType.EGRESS,
                ),
                Community(
                    name="Example 3",
                    slug="example-3",
                    value="64500:3",
                    type=CommunityType.EGRESS,
                ),
            ]
        )


class ConfigurationTest(StandardAPITestCases.View):
    model = Configuration
    brief_fields = ["id", "url", "display", "name"]
    create_data = [
        {"name": "Test1", "template": "test1_template"},
        {"name": "Test2", "template": "test2_template"},
        {"name": "Test3", "template": "test3_template"},
    ]
    bulk_update_data = {"template": "{{ router.hostname }}"}

    @classmethod
    def setUpTestData(cls):
        Configuration.objects.bulk_create(
            [
                Configuration(name="Example 1", template="example_1"),
                Configuration(name="Example 2", template="example_2"),
                Configuration(name="Example 3", template="example_3"),
            ]
        )


class DirectPeeringSessionTest(StandardAPITestCases.View):
    model = DirectPeeringSession
    brief_fields = ["id", "url", "display", "ip_address", "enabled"]
    bulk_update_data = {"enabled": False}

    @classmethod
    def setUpTestData(cls):
        local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        autonomous_system = AutonomousSystem.objects.create(asn=64500, name="Dummy")
        DirectPeeringSession.objects.bulk_create(
            [
                DirectPeeringSession(
                    local_autonomous_system=local_autonomous_system,
                    autonomous_system=autonomous_system,
                    relationship=BGPRelationship.PRIVATE_PEERING,
                    ip_address="2001:db8::1",
                    password="mypassword",
                ),
                DirectPeeringSession(
                    local_autonomous_system=local_autonomous_system,
                    autonomous_system=autonomous_system,
                    relationship=BGPRelationship.PRIVATE_PEERING,
                    ip_address="2001:db8::2",
                ),
                DirectPeeringSession(
                    local_autonomous_system=local_autonomous_system,
                    autonomous_system=autonomous_system,
                    relationship=BGPRelationship.PRIVATE_PEERING,
                    ip_address="2001:db8::3",
                ),
            ]
        )
        cls.create_data = [
            {
                "service_reference": "PNI-0001",
                "local_autonomous_system": local_autonomous_system.pk,
                "autonomous_system": autonomous_system.pk,
                "relationship": BGPRelationship.PRIVATE_PEERING,
                "ip_address": "198.51.100.1",
            },
            {
                "local_autonomous_system": local_autonomous_system.pk,
                "autonomous_system": autonomous_system.pk,
                "relationship": BGPRelationship.PRIVATE_PEERING,
                "ip_address": "198.51.100.2",
            },
            {
                "local_autonomous_system": local_autonomous_system.pk,
                "autonomous_system": autonomous_system.pk,
                "relationship": BGPRelationship.PRIVATE_PEERING,
                "ip_address": "198.51.100.3",
            },
        ]


class EmailTest(StandardAPITestCases.View):
    model = Email
    brief_fields = ["id", "url", "display", "name"]
    create_data = [
        {"name": "Test1", "subject": "test1_subject", "template": "test1_template"},
        {"name": "Test2", "subject": "test2_subject", "template": "test2_template"},
        {"name": "Test3", "subject": "test3_subject", "template": "test3_template"},
    ]
    bulk_update_data = {"template": "{{ autonomous_system.asn }}"}

    @classmethod
    def setUpTestData(cls):
        Email.objects.bulk_create(
            [
                Email(name="Example 1", subject="Example 1", template="example_1"),
                Email(name="Example 2", subject="Example 2", template="example_2"),
                Email(name="Example 3", subject="Example 3", template="example_3"),
            ]
        )


class InternetExchangeTest(StandardAPITestCases.View):
    model = InternetExchange
    brief_fields = ["id", "url", "display", "name", "slug"]
    bulk_update_data = {"comments": "Awesome IXP"}

    @classmethod
    def setUpTestData(cls):
        cls.local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        InternetExchange.objects.bulk_create(
            [
                InternetExchange(
                    name="Example 1",
                    slug="example-1",
                    local_autonomous_system=cls.local_autonomous_system,
                ),
                InternetExchange(
                    name="Example 2",
                    slug="example-2",
                    local_autonomous_system=cls.local_autonomous_system,
                ),
                InternetExchange(
                    name="Example 3",
                    slug="example-3",
                    local_autonomous_system=cls.local_autonomous_system,
                ),
            ]
        )
        cls.internet_exchange = InternetExchange.objects.get(slug="example-1")
        cls.create_data = [
            {
                "name": "Test1",
                "slug": "test1",
                "local_autonomous_system": cls.local_autonomous_system.pk,
            },
            {
                "name": "Test2",
                "slug": "test2",
                "local_autonomous_system": cls.local_autonomous_system.pk,
            },
            {
                "name": "Test3",
                "slug": "test3",
                "local_autonomous_system": cls.local_autonomous_system.pk,
            },
        ]

    def test_available_peers(self):
        url = reverse(
            "peering-api:internetexchange-available-peers",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.get(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_import_sessions(self):
        url = reverse(
            "peering-api:internetexchange-import-sessions",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)

    def test_prefixes(self):
        url = reverse(
            "peering-api:internetexchange-prefixes",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.get(url, **self.header)

        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data["prefixes"], [])

    def test_poll_peering_sessions(self):
        url = reverse(
            "peering-api:internetexchange-poll-peering-sessions",
            kwargs={"pk": self.internet_exchange.pk},
        )
        response = self.client.post(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)


class InternetExchangePeeringSessionTest(StandardAPITestCases.View):
    model = InternetExchangePeeringSession
    brief_fields = [
        "id",
        "url",
        "display",
        "ip_address",
        "enabled",
        "is_route_server",
    ]
    bulk_update_data = {"enabled": False}

    @classmethod
    def setUpTestData(cls):
        local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        autonomous_system = AutonomousSystem.objects.create(asn=64500, name="Dummy")
        ixp = InternetExchange.objects.create(
            name="Test", slug="test", local_autonomous_system=local_autonomous_system
        )
        ixp_connection = Connection.objects.create(
            vlan=2000, internet_exchange_point=ixp
        )

        InternetExchangePeeringSession.objects.bulk_create(
            [
                InternetExchangePeeringSession(
                    autonomous_system=autonomous_system,
                    ixp_connection=ixp_connection,
                    ip_address="2001:db8::1",
                    password="mypassword",
                ),
                InternetExchangePeeringSession(
                    autonomous_system=autonomous_system,
                    ixp_connection=ixp_connection,
                    ip_address="2001:db8::2",
                ),
                InternetExchangePeeringSession(
                    autonomous_system=autonomous_system,
                    ixp_connection=ixp_connection,
                    ip_address="2001:db8::3",
                ),
            ]
        )
        cls.create_data = [
            {
                "service_reference": "IXP-0001",
                "autonomous_system": autonomous_system.pk,
                "ixp_connection": ixp_connection.pk,
                "ip_address": "198.51.100.1",
            },
            {
                "autonomous_system": autonomous_system.pk,
                "ixp_connection": ixp_connection.pk,
                "ip_address": "198.51.100.2",
            },
            {
                "autonomous_system": autonomous_system.pk,
                "ixp_connection": ixp_connection.pk,
                "ip_address": "198.51.100.3",
            },
        ]


class RouterTest(StandardAPITestCases.View):
    model = Router
    brief_fields = ["id", "url", "display", "name", "hostname"]
    bulk_update_data = {"device_state": DeviceState.MAINTENANCE}

    @classmethod
    def setUpTestData(cls):
        cls.local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        cls.platform = Platform.objects.create(name="No Bugs OS", slug="nobugsos")
        cls.template = Configuration.objects.create(
            name="Test", template="Nothing useful"
        )
        Router.objects.bulk_create(
            [
                Router(
                    name="Example 1",
                    hostname="1.example.com",
                    device_state=DeviceState.ENABLED,
                    configuration_template=cls.template,
                    local_autonomous_system=cls.local_autonomous_system,
                ),
                Router(
                    name="Example 2",
                    hostname="2.example.com",
                    device_state=DeviceState.ENABLED,
                    configuration_template=cls.template,
                    local_autonomous_system=cls.local_autonomous_system,
                ),
                Router(
                    name="Example 3",
                    hostname="3.example.com",
                    device_state=DeviceState.ENABLED,
                    configuration_template=cls.template,
                    local_autonomous_system=cls.local_autonomous_system,
                ),
            ]
        )
        cls.router = Router.objects.get(hostname="1.example.com")
        cls.create_data = [
            {
                "name": "Test 1",
                "hostname": "test1.example.com",
                "device_state": DeviceState.ENABLED,
                "configuration_template": cls.template.pk,
                "local_autonomous_system": cls.local_autonomous_system.pk,
                "platform": cls.platform.pk,
            },
            {
                "name": "Test 2",
                "hostname": "test2.example.com",
                "device_state": DeviceState.MAINTENANCE,
                "configuration_template": cls.template.pk,
                "local_autonomous_system": cls.local_autonomous_system.pk,
                "platform": cls.platform.pk,
            },
            {
                "name": "Test 3",
                "hostname": "test3.example.com",
                "device_state": DeviceState.DISABLED,
                "configuration_template": cls.template.pk,
                "local_autonomous_system": cls.local_autonomous_system.pk,
                "platform": cls.platform.pk,
            },
        ]

    def test_configuration(self):
        url = reverse("peering-api:router-configuration", kwargs={"pk": self.router.pk})
        response = self.client.get(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)

    def test_test_napalm_connection(self):
        url = reverse(
            "peering-api:router-test-napalm-connection", kwargs={"pk": self.router.pk}
        )
        response = self.client.get(url, **self.header)
        self.assertHttpStatus(response, status.HTTP_202_ACCEPTED)


class RoutingPolicyTest(StandardAPITestCases.View):
    model = RoutingPolicy
    brief_fields = ["id", "url", "display", "name", "slug", "type"]
    create_data = [
        {
            "name": "Test1",
            "slug": "test1",
            "type": RoutingPolicyType.EXPORT,
            "weight": 1,
        },
        {
            "name": "Test2",
            "slug": "test2",
            "type": RoutingPolicyType.EXPORT,
            "weight": 2,
        },
        {
            "name": "Test3",
            "slug": "test3",
            "type": RoutingPolicyType.IMPORT_EXPORT,
            "weight": 3,
        },
    ]
    bulk_update_data = {"comments": "Awesome routing policy"}

    @classmethod
    def setUpTestData(cls):
        RoutingPolicy.objects.bulk_create(
            [
                RoutingPolicy(
                    name="Example 1",
                    slug="example-1",
                    type=RoutingPolicyType.EXPORT,
                    weight=0,
                ),
                RoutingPolicy(
                    name="Example 2",
                    slug="example-2",
                    type=RoutingPolicyType.IMPORT,
                    weight=0,
                ),
                RoutingPolicy(
                    name="Example 3",
                    slug="example-3",
                    type=RoutingPolicyType.EXPORT,
                    weight=0,
                ),
            ]
        )
