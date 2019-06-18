from django.db import transaction
from django.urls.exceptions import NoReverseMatch

from peering.constants import (
    COMMUNITY_TYPE_INGRESS,
    ROUTING_POLICY_TYPE_IMPORT,
    ROUTING_POLICY_TYPE_EXPORT,
)
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)

from utils.tests import ViewTestCase


class AutonomousSystemTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()

        self.model = AutonomousSystem
        self.asn = 29467
        self.as_name = "LuxNetwork S.A."
        self.autonomous_system = AutonomousSystem.objects.create(
            asn=self.asn, name=self.as_name, comment="This is a comment"
        )

    def test_as_list_view(self):
        with transaction.atomic():
            for i in range(50):
                AutonomousSystem.objects.create(
                    asn=(64500 + i), name="Test {}".format(i)
                )
        self.get_request("peering:autonomous_system_list", data={"q": 29467})

    def test_as_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request("peering:autonomous_system_add", expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request("peering:autonomous_system_add", contains="Create")

        # Try to create an object with valid data
        as_to_create = {"asn": 64500, "name": "as-created"}
        self.post_request("peering:autonomous_system_add", data=as_to_create)
        self.does_object_exist(as_to_create)

        # Try to create an object with invalid data
        as_not_to_create = {"asn": 64501}
        self.post_request("peering:autonomous_system_add", data=as_not_to_create)
        self.does_object_not_exist(as_not_to_create)

    def test_as_details_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:autonomous_system_details")

        # Using a wrong AS number, status should be 404 not found
        self.get_request(
            "peering:autonomous_system_details",
            params={"asn": 64500},
            expected_status_code=404,
        )

        # Using an existing AS, status should be 200 and the name of the AS
        # should be somewhere in the HTML code
        self.get_request(
            "peering:autonomous_system_details",
            params={"asn": self.asn},
            contains="LuxNetwork",
        )

    def test_as_edit_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:autonomous_system_edit")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:autonomous_system_edit",
            params={"asn": self.asn},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:autonomous_system_edit",
            params={"asn": self.asn},
            contains="Update",
        )

        # Still authenticated, wrong AS should be 404 not found
        self.get_request(
            "peering:autonomous_system_edit",
            params={"asn": 64500},
            expected_status_code=404,
        )

    def test_as_delete_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:autonomous_system_delete")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:autonomous_system_delete",
            params={"asn": self.asn},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:autonomous_system_delete",
            params={"asn": self.asn},
            contains="Confirm",
        )

        # Still authenticated, wrong AS should be 404 not found
        self.get_request(
            "peering:autonomous_system_delete",
            params={"asn": 64500},
            expected_status_code=404,
        )

    def test_as_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:autonomous_system_bulk_delete", expected_status_code=302
        )

    def test_as_direct_peering_sessions_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:autonomous_system_direct_peering_sessions")

        # Using a wrong AS number, status should be 404 not found
        self.get_request(
            "peering:autonomous_system_direct_peering_sessions",
            params={"asn": 64500},
            expected_status_code=404,
        )

        # Using an existing AS, status should be OK
        self.get_request(
            "peering:autonomous_system_direct_peering_sessions",
            params={"asn": self.asn},
            data={"q": "test"},
        )

    def test_as_internet_exchange_peering_sessions_view(self):
        # No ASN given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request(
                "peering:autonomous_system_internet_exchange_peering_sessions"
            )

        # Using a wrong AS number, status should be 404 not found
        self.get_request(
            "peering:autonomous_system_internet_exchange_peering_sessions",
            params={"asn": 64500},
            expected_status_code=404,
        )

        # Using an existing AS, status should be OK
        self.get_request(
            "peering:autonomous_system_internet_exchange_peering_sessions",
            params={"asn": self.asn},
            data={"q": "test"},
        )


class BGPGroupTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()

        self.model = BGPGroup
        self.name = "Test Group"
        self.slug = "test-group"
        self.bgp_group = BGPGroup.objects.create(name=self.name, slug=self.slug)
        self.asn = AutonomousSystem.objects.create(asn=64500, name="Test")
        self.session = DirectPeeringSession.objects.create(
            autonomous_system=self.asn,
            ip_address="2001:db8::1",
            bgp_group=self.bgp_group,
        )
        self.community = Community.objects.create(name="Test", value="64500:1")
        self.routing_policy = RoutingPolicy.objects.create(
            name="Test", slug="test", type=ROUTING_POLICY_TYPE_EXPORT, weight=0
        )

    def test_bgp_group_list_view(self):
        self.get_request("peering:bgp_group_list", data={"q": "test"})

    def test_bgp_group_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request("peering:bgp_group_add", expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request("peering:bgp_group_add", contains="Create")

        # Try to create an object with valid data
        bgp_group_to_create = {"name": "bgp-group-created", "slug": "bgp-group-created"}
        self.post_request("peering:bgp_group_add", data=bgp_group_to_create)
        self.does_object_exist(bgp_group_to_create)

        # Try to create an object with invalid data
        bgp_group_not_to_create = {"name": "bgp-group-notcreated"}
        self.post_request("peering:bgp_group_add", data=bgp_group_not_to_create)
        self.does_object_not_exist(bgp_group_not_to_create)

    def test_bgp_group_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request("peering:bgp_group_bulk_delete", expected_status_code=302)

    def test_bgp_group_details_view(self):
        # No slug given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:bgp_group_details")

        # Using a wrong slug, status should be 404 not found
        self.get_request(
            "peering:bgp_group_details",
            params={"slug": "not-found"},
            expected_status_code=404,
        )

        # Using an existing slug, status should be 200 and the name of the IX
        # should be somewhere in the HTML code
        self.get_request(
            "peering:bgp_group_details", params={"slug": self.slug}, contains=self.name
        )

    def test_bgp_group_edit_view(self):
        # No slug given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:bgp_group_edit")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:bgp_group_edit",
            params={"slug": self.slug},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:bgp_group_edit", params={"slug": self.slug}, contains="Update"
        )

        # Still authenticated, wrong slug should be 404 not found
        self.get_request(
            "peering:bgp_group_edit",
            params={"slug": "not-found"},
            expected_status_code=404,
        )

    def test_bgp_group_delete_view(self):
        # No slug given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:bgp_group_delete")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:bgp_group_delete",
            params={"slug": self.slug},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:bgp_group_delete", params={"slug": self.slug}, contains="Confirm"
        )

        # Still authenticated, wrong slug should be 404 not found
        self.get_request(
            "peering:bgp_group_delete",
            params={"slug": "not-found"},
            expected_status_code=404,
        )

    def test_bgp_group_peering_sessions_view(self):
        # Not logged in, 200 OK but not contains Add Peering Session button
        self.get_request(
            "peering:bgp_group_peering_sessions",
            params={"slug": self.slug},
            notcontains="Add a Peering Session",
        )

        # Authenticate and retry, 200 OK and should contains Add Peering
        # Session button
        self.authenticate_user()
        self.get_request(
            "peering:bgp_group_peering_sessions",
            params={"slug": self.slug},
            contains="Add",
        )

        # BGP Group not found
        self.get_request(
            "peering:bgp_group_peering_sessions",
            params={"slug": "not-found"},
            expected_status_code=404,
        )


class CommunityTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()

        self.model = Community
        self.name = "peering-all-exchanges"
        self.value = "64500:1"
        self.community = Community.objects.create(name=self.name, value=self.value)

    def test_community_list_view(self):
        self.get_request("peering:community_list", data={"q": "peering"})

    def test_community_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request("peering:community_add", expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request("peering:community_add", contains="Create")

        # Try to create an object with valid data
        community_to_create = {
            "name": "community-created",
            "value": "64500:1",
            "type": COMMUNITY_TYPE_INGRESS,
        }
        self.post_request("peering:community_add", data=community_to_create)
        self.does_object_exist(community_to_create)

        # Try to create an object with invalid data
        community_not_to_create = {"name": "community-not-created"}
        self.post_request("peering:community_add", data=community_not_to_create)
        self.does_object_not_exist(community_not_to_create)

    def test_community_details_view(self):
        # No community PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:community_details")

        # Using a wrong PK, status should be 404 not found
        self.get_request(
            "peering:community_details", params={"pk": 666}, expected_status_code=404
        )

        # Using an existing PK, status should be 200 and the name of the
        # community should be somewhere in the HTML code
        self.get_request(
            "peering:community_details",
            params={"pk": self.community.pk},
            contains=self.name,
        )

    def test_community_edit_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:community_edit")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:community_edit",
            params={"pk": self.community.pk},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:community_edit",
            params={"pk": self.community.pk},
            contains="Update",
        )

        # Still authenticated, wrong PK should be 404 not found
        self.get_request(
            "peering:community_edit", params={"pk": 2}, expected_status_code=404
        )

    def test_community_delete_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:community_delete")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:community_delete",
            params={"pk": self.community.pk},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:community_delete",
            params={"pk": self.community.pk},
            contains="Confirm",
        )

        # Still authenticated, wrong PK should be 404 not found
        self.get_request(
            "peering:community_delete", params={"pk": 2}, expected_status_code=404
        )

    def test_community_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request("peering:community_bulk_delete", expected_status_code=302)


class DirectPeeringSessionTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()

        self.model = DirectPeeringSession
        self.ip_address = "2001:db8::64:501"
        self.as64500 = AutonomousSystem.objects.create(asn=64500, name="Test")
        self.peering_session = DirectPeeringSession.objects.create(
            autonomous_system=self.as64500, ip_address=self.ip_address
        )

    def test_direct_peering_session_list_view(self):
        self.get_request("peering:direct_peering_session_list", data={"q": "test"})

    def test_direct_peering_session_details_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:direct_peering_session_details")

        # Using a wrong PK, status should be 404 not found
        self.get_request(
            "peering:direct_peering_session_details",
            params={"pk": 2},
            expected_status_code=404,
        )

        # Using an existing PK, status should be 200 and the name of the IP
        # should be somewhere in the HTML code
        self.get_request(
            "peering:direct_peering_session_details",
            params={"pk": self.peering_session.pk},
            contains=self.ip_address,
        )

    def test_direct_peering_session_edit_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:direct_peering_session_edit")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:direct_peering_session_edit",
            params={"pk": self.peering_session.pk},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:direct_peering_session_edit",
            params={"pk": self.peering_session.pk},
            contains="Update",
        )

        # Still authenticated, wrong PK should be 404 not found
        self.get_request(
            "peering:direct_peering_session_edit",
            params={"pk": 2},
            expected_status_code=404,
        )

    def test_direct_peering_session_delete_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:direct_peering_session_delete")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:direct_peering_session_delete",
            params={"pk": self.peering_session.pk},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:direct_peering_session_delete",
            params={"pk": self.peering_session.pk},
            contains="Confirm",
        )

        # Still authenticated, wrong router should be 404 not found
        self.get_request(
            "peering:direct_peering_session_delete",
            params={"pk": 2},
            expected_status_code=404,
        )

    def test_direct_peering_session_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:direct_peering_session_bulk_delete", expected_status_code=302
        )


class InternetExchangeTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()

        self.model = InternetExchange
        self.name = "Test IX"
        self.slug = "test-ix"
        self.ix = InternetExchange.objects.create(name=self.name, slug=self.slug)
        self.asn = AutonomousSystem.objects.create(asn=64500, name="Test")
        self.session = InternetExchangePeeringSession.objects.create(
            internet_exchange=self.ix,
            autonomous_system=self.asn,
            ip_address="2001:db8::1",
        )
        self.community = Community.objects.create(name="Test", value="64500:1")
        self.routing_policy = RoutingPolicy.objects.create(
            name="Test", slug="test", type=ROUTING_POLICY_TYPE_EXPORT, weight=0
        )

    def test_ix_list_view(self):
        self.get_request("peering:internet_exchange_list", data={"q": "test"})

    def test_ix_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request("peering:internet_exchange_add", expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request("peering:internet_exchange_add", contains="Create")

        # Try to create an object with valid data
        ix_to_create = {"name": "ix-created", "slug": "ix-created"}
        self.post_request("peering:internet_exchange_add", data=ix_to_create)
        self.does_object_exist(ix_to_create)

        # Try to create an object with invalid data
        ix_not_to_create = {"name": "ix-notcreated"}
        self.post_request("peering:internet_exchange_add", data=ix_not_to_create)
        self.does_object_not_exist(ix_not_to_create)

    def test_ix_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:internet_exchange_bulk_delete", expected_status_code=302
        )

    def test_ix_details_view(self):
        # No slug given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:internet_exchange_details")

        # Using a wrong slug, status should be 404 not found
        self.get_request(
            "peering:internet_exchange_details",
            params={"slug": "not-found"},
            expected_status_code=404,
        )

        # Using an existing slug, status should be 200 and the name of the IX
        # should be somewhere in the HTML code
        self.get_request(
            "peering:internet_exchange_details",
            params={"slug": self.slug},
            contains=self.name,
        )

    def test_ix_edit_view(self):
        # No slug given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:internet_exchange_edit")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:internet_exchange_edit",
            params={"slug": self.slug},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:internet_exchange_edit",
            params={"slug": self.slug},
            contains="Update",
        )

        # Still authenticated, wrong slug should be 404 not found
        self.get_request(
            "peering:internet_exchange_edit",
            params={"slug": "not-found"},
            expected_status_code=404,
        )

    def test_ix_delete_view(self):
        # No slug given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:internet_exchange_delete")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:internet_exchange_delete",
            params={"slug": self.slug},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:internet_exchange_delete",
            params={"slug": self.slug},
            contains="Confirm",
        )

        # Still authenticated, wrong slug should be 404 not found
        self.get_request(
            "peering:internet_exchange_delete",
            params={"slug": "not-found"},
            expected_status_code=404,
        )

    def test_internet_exchange_peering_sessions_view(self):
        # Not logged in, 200 OK but not contains Add Peering Session button
        self.get_request(
            "peering:internet_exchange_peering_sessions",
            params={"slug": self.slug},
            notcontains="Add a Peering Session",
        )

        # Authenticate and retry, 200 OK and should contains Add Peering
        # Session button
        self.authenticate_user()
        self.get_request(
            "peering:internet_exchange_peering_sessions",
            params={"slug": self.slug},
            contains="Add",
        )

        # IX not found
        self.get_request(
            "peering:internet_exchange_peering_sessions",
            params={"slug": "not-found"},
            expected_status_code=404,
        )


class InternetExchangePeeringSessionTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()

        self.model = InternetExchangePeeringSession
        self.ip_address = "2001:db8::64:501"
        self.as64500 = AutonomousSystem.objects.create(asn=64500, name="Test")
        self.ix = InternetExchange.objects.create(name="Test", slug="test")
        self.peering_session = InternetExchangePeeringSession.objects.create(
            autonomous_system=self.as64500,
            internet_exchange=self.ix,
            ip_address=self.ip_address,
        )

    def test_internet_exchange_peering_session_list_view(self):
        self.get_request(
            "peering:internet_exchange_peering_session_list", data={"q": "test"}
        )

    def test_internet_exchange_peering_session_details_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:internet_exchange_peering_session_details")

        # Using a wrong PK, status should be 404 not found
        self.get_request(
            "peering:internet_exchange_peering_session_details",
            params={"pk": 2},
            expected_status_code=404,
        )

        # Using an existing PK, status should be 200 and the name of the IP
        # should be somewhere in the HTML code
        self.get_request(
            "peering:internet_exchange_peering_session_details",
            params={"pk": self.peering_session.pk},
            contains=self.ip_address,
        )

    def test_internet_exchange_peering_session_edit_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:internet_exchange_peering_session_edit")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:internet_exchange_peering_session_edit",
            params={"pk": self.peering_session.pk},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:internet_exchange_peering_session_edit",
            params={"pk": self.peering_session.pk},
            contains="Update",
        )

        # Still authenticated, wrong PK should be 404 not found
        self.get_request(
            "peering:internet_exchange_peering_session_edit",
            params={"pk": 2},
            expected_status_code=404,
        )

    def test_internet_exchange_peering_session_delete_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:internet_exchange_peering_session_delete")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:internet_exchange_peering_session_delete",
            params={"pk": self.peering_session.pk},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:internet_exchange_peering_session_delete",
            params={"pk": self.peering_session.pk},
            contains="Confirm",
        )

        # Still authenticated, wrong router should be 404 not found
        self.get_request(
            "peering:internet_exchange_peering_session_delete",
            params={"pk": 2},
            expected_status_code=404,
        )

    def test_internet_exchange_peering_session_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:internet_exchange_peering_session_bulk_delete",
            expected_status_code=302,
        )


class RouterTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()

        self.model = Router
        self.name = "test.router"
        self.hostname = "test.router.example.org"
        self.router = Router.objects.create(name=self.name, hostname=self.hostname)

    def test_router_list_view(self):
        with transaction.atomic():
            for i in range(500):
                Router.objects.create(
                    name="Test {}".format(i), hostname="test{}.example.com".format(i)
                )
        self.get_request("peering:router_list", data={"q": "test"})

    def test_router_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request("peering:router_add", expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request("peering:router_add", contains="Create")

        # Try to create an object with valid data
        router_to_create = {
            "netbox_device_id": 0,
            "name": "router.created",
            "hostname": "router.created.example.com",
        }
        self.post_request("peering:router_add", data=router_to_create)
        self.does_object_exist(router_to_create)

        # Try to create an object with invalid data
        router_not_to_create = {"name": "router.notcreated"}
        self.post_request("peering:router_add", data=router_not_to_create)
        self.does_object_not_exist(router_not_to_create)

    def test_router_details_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:router_details")

        # Using a wrong PK, status should be 404 not found
        self.get_request(
            "peering:router_details", params={"pk": 2}, expected_status_code=404
        )

        # Using an existing PK, status should be 200 and the name of the router
        # should be somewhere in the HTML code
        self.get_request(
            "peering:router_details", params={"pk": self.router.pk}, contains=self.name
        )

    def test_router_edit_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:router_edit")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:router_edit",
            params={"pk": self.router.pk},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:router_edit", params={"pk": self.router.pk}, contains="Update"
        )

        # Still authenticated, wrong PK should be 404 not found
        self.get_request(
            "peering:router_edit", params={"pk": 2}, expected_status_code=404
        )

    def test_router_delete_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:router_delete")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:router_delete",
            params={"pk": self.router.pk},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:router_delete", params={"pk": self.router.pk}, contains="Confirm"
        )

        # Still authenticated, wrong router should be 404 not found
        self.get_request(
            "peering:router_delete", params={"pk": 2}, expected_status_code=404
        )

    def test_router_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request("peering:router_bulk_delete", expected_status_code=302)


class RoutingPolicyTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()

        self.model = RoutingPolicy
        self.name = "Export Policy"
        self.slug = "export-policy"
        self.routing_policy = RoutingPolicy.objects.create(
            name=self.name, slug=self.slug, type=ROUTING_POLICY_TYPE_EXPORT, weight=0
        )

    def test_routing_policy_list_view(self):
        self.get_request("peering:routing_policy_list", data={"q": "export"})

    def test_routing_policy_add_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request("peering:routing_policy_add", expected_status_code=302)

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request("peering:routing_policy_add", contains="Create")

        # Try to create an object with valid data
        routing_policy_to_create = {
            "name": "Import Policy",
            "slug": "import-policy",
            "type": ROUTING_POLICY_TYPE_IMPORT,
            "weight": 0,
            "address_family": 0,
        }
        self.post_request("peering:routing_policy_add", data=routing_policy_to_create)
        self.does_object_exist(routing_policy_to_create)

        # Try to create an object with invalid data
        routing_policy_not_to_create = {"name": "routing-policy-not-created"}
        self.post_request(
            "peering:routing_policy_add", data=routing_policy_not_to_create
        )
        self.does_object_not_exist(routing_policy_not_to_create)

    def test_routing_policy_details_view(self):
        # No routing policy PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:routing_policy_details")

        # Using a wrong PK, status should be 404 not found
        self.get_request(
            "peering:routing_policy_details",
            params={"pk": 666},
            expected_status_code=404,
        )

        # Using an existing PK, status should be 200 and the name of the
        # routing policy should be somewhere in the HTML code
        self.get_request(
            "peering:routing_policy_details",
            params={"pk": self.routing_policy.pk},
            contains=self.name,
        )

    def test_routing_policy_edit_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:routing_policy_edit")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:routing_policy_edit",
            params={"pk": self.routing_policy.pk},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:routing_policy_edit",
            params={"pk": self.routing_policy.pk},
            contains="Update",
        )

        # Still authenticated, wrong PK should be 404 not found
        self.get_request(
            "peering:routing_policy_edit", params={"pk": 2}, expected_status_code=404
        )

    def test_routing_policy_delete_view(self):
        # No PK given, view should not work
        with self.assertRaises(NoReverseMatch):
            self.get_request("peering:routing_policy_delete")

        # Not logged in, no right to access the view, should be redirected
        self.get_request(
            "peering:routing_policy_delete",
            params={"pk": self.routing_policy.pk},
            expected_status_code=302,
        )

        # Authenticate and retry, should be OK
        self.authenticate_user()
        self.get_request(
            "peering:routing_policy_delete",
            params={"pk": self.routing_policy.pk},
            contains="Confirm",
        )

        # Still authenticated, wrong PK should be 404 not found
        self.get_request(
            "peering:routing_policy_delete", params={"pk": 2}, expected_status_code=404
        )

    def test_routing_policy_bulk_delete_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request("peering:routing_policy_bulk_delete", expected_status_code=302)

    def test_routing_policy_bulk_edit_view(self):
        # Not logged in, no right to access the view, should be redirected
        self.get_request("peering:routing_policy_bulk_edit", expected_status_code=302)
