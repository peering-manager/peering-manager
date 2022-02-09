from collections import OrderedDict

from devices.filters import ConfigurationFilterSet
from devices.models import Configuration
from devices.tables import ConfigurationTable
from messaging.filters import ContactFilterSet, EmailFilterSet
from messaging.models import Contact, ContactAssignment, Email
from messaging.tables import ContactTable, EmailTable
from net.filters import ConnectionFilterSet
from net.models import Connection
from net.tables import ConnectionTable
from peering.filters import (
    AutonomousSystemFilterSet,
    BGPGroupFilterSet,
    CommunityFilterSet,
    DirectPeeringSessionFilterSet,
    InternetExchangeFilterSet,
    InternetExchangePeeringSessionFilterSet,
    RouterFilterSet,
    RoutingPolicyFilterSet,
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
from peering.tables import (
    AutonomousSystemTable,
    BGPGroupTable,
    CommunityTable,
    DirectPeeringSessionTable,
    InternetExchangePeeringSessionTable,
    InternetExchangeTable,
    RouterTable,
    RoutingPolicyTable,
)
from utils.functions import count_related

__all__ = ("SEARCH_MAX_RESULTS", "SEARCH_TYPES")

SEARCH_MAX_RESULTS = 15
SEARCH_TYPES = OrderedDict(
    (
        # devices
        (
            "configuration",
            {
                "queryset": Configuration.objects.all(),
                "filterset": ConfigurationFilterSet,
                "table": ConfigurationTable,
                "url": "devices:configuration_list",
            },
        ),
        # messaging
        (
            "contact",
            {
                "queryset": Contact.objects.prefetch_related("assignments").annotate(
                    assignment_count=count_related(ContactAssignment, "contact")
                ),
                "filterset": ContactFilterSet,
                "table": ContactTable,
                "url": "messaging:contact_list",
            },
        ),
        (
            "email",
            {
                "queryset": Email.objects.all(),
                "filterset": EmailFilterSet,
                "table": EmailTable,
                "url": "messaging:email_list",
            },
        ),
        # net
        (
            "connection",
            {
                "queryset": Connection.objects.prefetch_related(
                    "internet_exchange_point", "router"
                ),
                "filterset": ConnectionFilterSet,
                "table": ConnectionTable,
                "url": "net:connection_list",
            },
        ),
        # peering
        (
            "autonomousystem",
            {
                "queryset": AutonomousSystem.objects.defer("prefixes"),
                "filterset": AutonomousSystemFilterSet,
                "table": AutonomousSystemTable,
                "url": "peering:autonomoussystem_list",
            },
        ),
        (
            "bgpgroup",
            {
                "queryset": BGPGroup.objects.all(),
                "filterset": BGPGroupFilterSet,
                "table": BGPGroupTable,
                "url": "peering:bgpgroup_list",
            },
        ),
        (
            "community",
            {
                "queryset": Community.objects.all(),
                "filterset": CommunityFilterSet,
                "table": CommunityTable,
                "url": "peering:community_list",
            },
        ),
        (
            "directpeeringsession",
            {
                "queryset": DirectPeeringSession.objects.prefetch_related(
                    "autonomous_system", "bgp_group", "router"
                ),
                "filterset": DirectPeeringSessionFilterSet,
                "table": DirectPeeringSessionTable,
                "url": "peering:directpeeringsession_list",
            },
        ),
        (
            "internetexchange",
            {
                "queryset": InternetExchange.objects.prefetch_related(
                    "local_autonomous_system"
                ).annotate(
                    connection_count=count_related(
                        Connection, "internet_exchange_point"
                    )
                ),
                "filterset": InternetExchangeFilterSet,
                "table": InternetExchangeTable,
                "url": "peering:internetexchange_list",
            },
        ),
        (
            "internetexchangepeeringsession",
            {
                "queryset": InternetExchangePeeringSession.objects.prefetch_related(
                    "autonomous_system", "ixp_connection"
                ),
                "filterset": InternetExchangePeeringSessionFilterSet,
                "table": InternetExchangePeeringSessionTable,
                "url": "peering:internetexchangepeeringsession_list",
            },
        ),
        (
            "router",
            {
                "queryset": Router.objects.prefetch_related("platform").annotate(
                    connection_count=count_related(Connection, "router")
                ),
                "filterset": RouterFilterSet,
                "table": RouterTable,
                "url": "peering:router_list",
            },
        ),
        (
            "routingpolicy",
            {
                "queryset": RoutingPolicy.objects.all(),
                "filterset": RoutingPolicyFilterSet,
                "table": RoutingPolicyTable,
                "url": "peering:routingpolicy_list",
            },
        ),
    ),
)
