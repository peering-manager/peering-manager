from collections import OrderedDict

from bgp.filtersets import CommunityFilterSet
from bgp.models import Community
from bgp.tables import CommunityTable
from devices.filtersets import ConfigurationFilterSet, RouterFilterSet
from devices.models import Configuration, Router
from devices.tables import ConfigurationTable, RouterTable
from messaging.filtersets import ContactFilterSet, EmailFilterSet
from messaging.models import Contact, ContactAssignment, Email
from messaging.tables import ContactTable, EmailTable
from net.filtersets import BFDFilterSet, ConnectionFilterSet
from net.models import BFD, Connection
from net.tables import BFDTable, ConnectionTable
from peering.filtersets import (
    AutonomousSystemFilterSet,
    BGPGroupFilterSet,
    DirectPeeringSessionFilterSet,
    InternetExchangeFilterSet,
    InternetExchangePeeringSessionFilterSet,
    RoutingPolicyFilterSet,
)
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)
from peering.tables import (
    AutonomousSystemTable,
    BGPGroupTable,
    DirectPeeringSessionTable,
    InternetExchangePeeringSessionTable,
    InternetExchangeTable,
    RoutingPolicyTable,
)
from utils.functions import count_related

__all__ = ("NESTED_SERIALIZER_PREFIX", "SEARCH_MAX_RESULTS", "SEARCH_TYPES")

# Prefix for nested serializers
NESTED_SERIALIZER_PREFIX = "Nested"

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
            "bfd",
            {
                "queryset": BFD.objects.all(),
                "filterset": BFDFilterSet,
                "table": BFDTable,
                "url": "net:bfd_list",
            },
        ),
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
                "queryset": AutonomousSystem.objects.all().annotate(
                    directpeeringsession_count=count_related(
                        DirectPeeringSession, "autonomous_system"
                    ),
                    internetexchangepeeringsession_count=count_related(
                        InternetExchangePeeringSession, "autonomous_system"
                    ),
                ),
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
                "url": "bgp:community_list",
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
                "url": "devices:router_list",
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
