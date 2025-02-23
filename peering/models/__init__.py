import ipaddress
import logging

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from netfields import InetAddressField

from net.models import Connection
from peering_manager.models import JournalingMixin, OrganisationalModel, PrimaryModel
from peeringdb.functions import get_shared_facilities, get_shared_internet_exchanges
from peeringdb.models import IXLanPrefix, Network, NetworkContact, NetworkIXLan

from ..enums import BGPState, CommunityType, IPFamily, RoutingPolicyType
from ..fields import ASNField, CommunityField
from ..functions import call_irr_as_set_resolver, get_community_kind, parse_irr_as_set
from .abstracts import *
from .mixins import *

__all__ = (
    "AutonomousSystem",
    "BGPGroup",
    "BGPSession",
    "Community",
    "DirectPeeringSession",
    "InternetExchange",
    "InternetExchangePeeringSession",
    "RoutingPolicy",
)

logger = logging.getLogger("peering.manager.peering")


class AutonomousSystem(PrimaryModel, PolicyMixin, JournalingMixin):
    asn = ASNField(unique=True, verbose_name="ASN")
    name = models.CharField(max_length=200)
    name_peeringdb_sync = models.BooleanField(default=True)
    irr_as_set = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="IRR AS-SET"
    )
    irr_as_set_peeringdb_sync = models.BooleanField(default=True)
    ipv6_max_prefixes = models.PositiveIntegerField(
        blank=True, null=True, default=0, verbose_name="IPv6 max prefix"
    )
    ipv6_max_prefixes_peeringdb_sync = models.BooleanField(default=True)
    ipv4_max_prefixes = models.PositiveIntegerField(
        blank=True, null=True, default=0, verbose_name="IPv4 max prefix"
    )
    ipv4_max_prefixes_peeringdb_sync = models.BooleanField(default=True)
    import_routing_policies = models.ManyToManyField(
        "RoutingPolicy", blank=True, related_name="%(class)s_import_routing_policies"
    )
    export_routing_policies = models.ManyToManyField(
        "RoutingPolicy", blank=True, related_name="%(class)s_export_routing_policies"
    )
    communities = models.ManyToManyField("Community", blank=True)
    prefixes = models.JSONField(blank=True, null=True, editable=False)
    affiliated = models.BooleanField(default=False)
    contacts = GenericRelation(to="messaging.ContactAssignment")

    class Meta:
        ordering = ["asn", "affiliated"]
        permissions = [("send_email", "Can send e-mails to AS contact")]

    @property
    def is_private(self):
        return (
            self.asn
            in (0, 23456, 65535, 4294967295)  # RFC 7607, RFC 4893, RFC 7300, RFC 7300
            or (self.asn >= 64496 and self.asn <= 64511)  # RFC 5398
            or (self.asn >= 64512 and self.asn <= 65534)  # RFC 6996
            or (self.asn >= 65536 and self.asn <= 65551)  # RFC 5398
            or (self.asn >= 65552 and self.asn <= 131071)  # RFC IANA
            or (self.asn >= 4200000000 and self.asn <= 4294967294)  # RFC 6996
        )

    @property
    def peeringdb_network(self):
        if self.is_private:
            return None

        try:
            return Network.objects.get(asn=self.asn)
        except Network.DoesNotExist:
            return None

    @property
    def general_policy(self):
        if self.peeringdb_network:
            return self.peeringdb_network.policy_general
        return None

    @property
    def peeringdb_contacts(self):
        if self.peeringdb_network:
            return NetworkContact.objects.filter(net=self.peeringdb_network)
        return NetworkContact.objects.none()

    @property
    def can_receive_email(self):
        return self.contacts.count() > 0 or self.peeringdb_contacts.count() > 0

    @staticmethod
    def create_from_peeringdb(asn):
        try:
            network = Network.objects.get(asn=asn)
        except Network.DoesNotExist:
            return None

        autonomous_system, _ = AutonomousSystem.objects.get_or_create(
            asn=network.asn,
            defaults={
                "name": network.name,
                "irr_as_set": network.irr_as_set,
                "ipv6_max_prefixes": network.info_prefixes6,
                "ipv4_max_prefixes": network.info_prefixes4,
            },
        )

        return autonomous_system

    def __str__(self):
        return f"AS{self.asn} - {self.name}"

    def export_policies(self):
        return self.export_routing_policies.all()

    def import_policies(self):
        return self.import_routing_policies.all()

    def get_absolute_url(self):
        return reverse("peering:autonomoussystem_view", args=[self.pk])

    def get_internet_exchange_peering_sessions_list_url(self):
        return reverse(
            "peering:autonomoussystem_internet_exchange_peering_sessions",
            args=[self.pk],
        )

    def get_direct_peering_sessions_list_url(self):
        return reverse(
            "peering:autonomoussystem_direct_peering_sessions", args=[self.pk]
        )

    def get_direct_peering_sessions(self, bgp_group=None):
        """
        Returns all direct peering sessions with this AS.
        """
        if bgp_group:
            return DirectPeeringSession.objects.filter(
                autonomous_system=self, bgp_group=bgp_group
            )
        return DirectPeeringSession.objects.filter(autonomous_system=self)

    def get_ixp_peering_sessions(self, internet_exchange_point=None):
        """
        Returns all IXP peering sessions with this AS.
        """
        sessions = InternetExchangePeeringSession.objects.filter(autonomous_system=self)
        if internet_exchange_point:
            return sessions.filter(
                ixp_connection__internet_exchange_point=internet_exchange_point
            )

        return sessions

    def get_internet_exchange_points(self, other):
        """
        Returns all IXPs this AS is peering on (with us).
        """
        return InternetExchange.objects.filter(
            pk__in=Connection.objects.filter(
                pk__in=self.get_ixp_peering_sessions().values_list(
                    "ixp_connection", flat=True
                )
            ).values_list("internet_exchange_point", flat=True),
            local_autonomous_system=other,
        )

    def get_shared_internet_exchange_points(self, other):
        """
        Returns all IXPs this AS has with the other one.
        """
        peeringdb_network_record = other
        local_autonomous_system = self
        if isinstance(other, self.__class__):
            peeringdb_network_record = other.peeringdb_network
            local_autonomous_system = other

        return InternetExchange.objects.filter(
            peeringdb_ixlan__id__in=get_shared_internet_exchanges(
                self.peeringdb_network, peeringdb_network_record
            ).values_list("id", flat=True),
            local_autonomous_system=local_autonomous_system,
        )

    def get_peeringdb_shared_facilities(self, other):
        peeringdb_network_record = other
        if type(other) is type(self):
            peeringdb_network_record = other.peeringdb_network

        return get_shared_facilities(self.peeringdb_network, peeringdb_network_record)

    def get_missing_peering_sessions(self, other, internet_exchange_point=None):
        """
        Returns all missing peering sessions between this AS and the other one on a
        given IXP. As we are relying on PeeringDB to discover sessions there are no
        points in doing so if the IXP is not linked to a PeeringDB record.

        If the IXP is not specified then missing peering sessions will be returned for
        all shared IXPs between this and the other AS.
        """
        if self == other or self.is_private:
            return NetworkIXLan.objects.none()

        filter = {"autonomous_system": self}
        if internet_exchange_point:
            filter["ixp_connection__id__in"] = (
                internet_exchange_point.get_connections().values_list("id", flat=True)
            )
        ip_addresses = InternetExchangePeeringSession.objects.filter(
            **filter
        ).values_list("ip_address", flat=True)

        qs_filter = Q(asn=self.asn) & (
            (Q(ipaddr6__isnull=False) & ~Q(ipaddr6__in=ip_addresses))
            | (Q(ipaddr4__isnull=False) & ~Q(ipaddr4__in=ip_addresses))
        )
        if internet_exchange_point:
            qs_filter &= Q(ixlan=internet_exchange_point.peeringdb_ixlan)
        else:
            qs_filter &= Q(
                ixlan__in=self.get_shared_internet_exchange_points(other).values_list(
                    "peeringdb_ixlan", flat=True
                )
            )
        return NetworkIXLan.objects.filter(qs_filter)

    def get_routers(self):
        """
        Returns all routers that have at least one BGP session with this autonomous
        system (direct or over IXP).
        """
        from devices.models import Router

        connections = Connection.objects.filter(
            pk__in=self.get_ixp_peering_sessions().values_list(
                "ixp_connection", flat=True
            )
        )
        routers = Router.objects.filter(
            pk__in=self.get_direct_peering_sessions().values_list("router", flat=True)
        )

        if connections:
            return routers.union(
                Router.objects.filter(
                    pk__in=connections.values_list("router", flat=True)
                )
            )

        return routers

    def are_bgp_sessions_pollable(self):
        """
        Returns whether or not BGP sessions can be polled for the autonomous system.

        If a router has its `poll_bgp_sessions_state` property set to a boolan true,
        BGP sessions are considered as pollable.
        """
        return any(router.poll_bgp_sessions_state for router in self.get_routers())

    def divergence_from_peeringdb(self):
        """
        Find out fields with values that differ from PeeringDB.
        """
        if self.is_private:
            return []

        network = self.peeringdb_network
        if not network:
            return []

        diff = []
        key_map = {
            "name": "name",
            "irr_as_set": "irr_as_set",
            "ipv6_max_prefixes": "info_prefixes6",
            "ipv4_max_prefixes": "info_prefixes4",
        }
        label_map = {
            "name": "Name",
            "irr_as_set": "IRR AS-SET",
            "ipv6_max_prefixes": "IPv6 Max Prefix",
            "ipv4_max_prefixes": "IPv4 Max Prefix",
        }

        for local_key, peeringdb_key in key_map.items():
            local_value = getattr(self, local_key)
            peeringdb_value = getattr(network, peeringdb_key)

            if local_value != peeringdb_value:
                diff.append(
                    {
                        "label": label_map[local_key],
                        "local_key": local_key,
                        "peeringdb_key": peeringdb_key,
                        "local_value": local_value,
                        "peeringdb_value": peeringdb_value,
                    }
                )

        return diff

    def synchronise_with_peeringdb(self):
        """
        Synchronises AS properties with those found in PeeringDB.
        """
        if self.is_private:
            return True

        network = self.peeringdb_network
        if not network:
            return False

        if self.name_peeringdb_sync:
            self.name = network.name
        if self.irr_as_set_peeringdb_sync:
            self.irr_as_set = network.irr_as_set
        if self.ipv6_max_prefixes_peeringdb_sync:
            self.ipv6_max_prefixes = network.info_prefixes6
        if self.ipv4_max_prefixes_peeringdb_sync:
            self.ipv4_max_prefixes = network.info_prefixes4

        try:
            self.save()
            return True
        except Exception:
            return False

    def retrieve_irr_as_set_prefixes(self):
        """
        Returns a prefix list for this AS' IRR AS-SET. If none is provided the
        function will try to look for a prefix list based on the AS number.

        This function will actually retrieve prefixes from IRR online sources. It is
        expected to be slow due to network operations and depending on the size of the
        data to process.
        """
        fallback = False
        as_sets = parse_irr_as_set(self.asn, self.irr_as_set)
        prefixes = {"ipv6": [], "ipv4": []}

        try:
            # For each AS-SET try getting IPv6 and IPv4 prefixes
            for as_set in as_sets:
                prefixes["ipv6"].extend(
                    call_irr_as_set_resolver(as_set, address_family=6)
                )
                prefixes["ipv4"].extend(
                    call_irr_as_set_resolver(as_set, address_family=4)
                )
        except ValueError:
            # Error parsing AS-SETs
            fallback = True

        # If fallback is triggered or no prefixes found, try prefix lookup by ASN
        if fallback or (not prefixes["ipv6"] and not prefixes["ipv4"]):
            logger.debug(
                f"falling back to AS number lookup to search for AS{self.asn} prefixes"
            )
            prefixes["ipv6"].extend(
                call_irr_as_set_resolver(f"AS{self.asn}", address_family=6)
            )
            prefixes["ipv4"].extend(
                call_irr_as_set_resolver(f"AS{self.asn}", address_family=4)
            )

        return prefixes

    def get_irr_as_set_prefixes(self, address_family=0):
        """
        Returns a prefix list for this AS' IRR AS-SET. If none is provided the list
        will be empty.

        If specified, only a list of the prefixes for the given address family will be
        returned. 6 for IPv6, 4 for IPv4, both for all other values.

        The stored database value will be used if it exists.
        """
        prefixes = (
            self.prefixes if self.prefixes else self.retrieve_irr_as_set_prefixes()
        )

        if address_family == 6:
            return prefixes["ipv6"]
        if address_family == 4:
            return prefixes["ipv4"]
        return prefixes

    def get_contact_email_addresses(self):
        """
        Returns a list of all contacts with their respective e-mails addresses.
        The returned list can be used in form choice fields.
        """
        addresses = []

        # Append the contact set by the user if one has been set
        for assigned in self.contacts.all():
            contact = assigned.contact
            if assigned.contact.email:
                addresses.append((contact.email, f"{contact.name} - {contact.email}"))

        # Append the contacts found in PeeringDB, avoid re-adding a contact if the
        # email address is the same as the one set by the user manually
        for contact in self.peeringdb_contacts:
            if contact.email and contact.email not in [a[0] for a in addresses]:
                addresses.append(
                    (
                        contact.email,
                        (
                            f"{contact.name} - {contact.email}"
                            if contact.name
                            else contact.email
                        ),
                    )
                )
        return addresses

    def get_cc_email_contacts(self):
        """
        Returns a list of user defined CC contacts from settings
        """
        addresses = []

        # Extract user defined addresses
        for email in settings.EMAIL_CC_CONTACTS:
            if isinstance(email, tuple):
                addresses.append(
                    (
                        email[0],
                        f"{email[1]} - {email[0]}" if len(email) > 1 else email[0],
                    )
                )
            else:
                addresses.append((email, email))
        return addresses

    def get_email_context(self):
        """
        Returns a dict, to be used in a Jinja2 environment, that holds enough data to
        help in creating an e-mail from a template.
        """
        affiliated = AutonomousSystem.objects.filter(affiliated=True)
        return {"affiliated_autonomous_systems": affiliated, "autonomous_system": self}

    def render_email(self, email):
        """
        Renders an e-mail from a template.
        """
        return email.render(self.get_email_context())


class BGPGroup(AbstractGroup):
    class Meta(AbstractGroup.Meta):
        ordering = ["name", "slug"]
        verbose_name = "BGP group"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("peering:bgpgroup_view", args=[self.pk])

    def get_peering_sessions_list_url(self):
        return reverse("peering:bgpgroup_peering_sessions", args=[self.pk])

    def get_peering_sessions(self):
        return DirectPeeringSession.objects.filter(bgp_group=self)

    def get_routers(self):
        from devices.models import Router

        return Router.objects.filter(
            pk__in=self.get_peering_sessions().values_list("router", flat=True)
        )


class Community(OrganisationalModel):
    value = CommunityField(max_length=50)
    type = models.CharField(max_length=50, choices=CommunityType, blank=True, null=True)

    class Meta:
        verbose_name_plural = "communities"
        ordering = ["value", "name"]

    @property
    def kind(self) -> str | None:
        if not settings.VALIDATE_BGP_COMMUNITY_VALUE:
            return None
        try:
            return get_community_kind(self.value)
        except ValueError:
            return None

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("peering:community_view", args=[self.pk])

    def get_type_html(self, display_name=False):
        if self.type == CommunityType.EGRESS:
            badge_type = "text-bg-primary"
            text = self.get_type_display()
        elif self.type == CommunityType.INGRESS:
            badge_type = "text-bg-info"
            text = self.get_type_display()
        else:
            badge_type = "text-bg-secondary"
            text = "Not set"

        if display_name:
            text = self.name

        return mark_safe(f'<span class="badge {badge_type}">{text}</span>')


class DirectPeeringSession(BGPSession):
    local_autonomous_system = models.ForeignKey(
        to="peering.AutonomousSystem",
        on_delete=models.CASCADE,
        related_name="%(class)s_local_autonomous_system",
        null=True,
    )
    local_ip_address = InetAddressField(
        store_prefix_length=True,
        blank=True,
        null=True,
        verbose_name="Local IP address",
    )
    ip_address = InetAddressField(store_prefix_length=True, verbose_name="IP address")
    bgp_group = models.ForeignKey(
        to="peering.BGPGroup",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="BGP group",
    )
    relationship = models.ForeignKey(to="bgp.Relationship", on_delete=models.PROTECT)
    router = models.ForeignKey(
        to="devices.Router", blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta(BGPSession.Meta):
        ordering = [
            "service_reference",
            "local_autonomous_system",
            "autonomous_system",
            "ip_address",
        ]

    def __str__(self):
        return f"{self.relationship} - AS{self.autonomous_system.asn} - IP {self.ip_address}"

    def get_absolute_url(self):
        return reverse("peering:directpeeringsession_view", args=[self.pk])

    def poll(self):
        if not self.router:
            logger.debug(
                f"cannot poll bgp session state for {self.ip_address}, no router"
            )
            return False

        state = self.router.poll_bgp_session(self.ip_address)
        if state:
            self.bgp_state = state["bgp_state"]
            self.received_prefix_count = state["received_prefix_count"]
            self.accepted_prefix_count = state["accepted_prefix_count"]
            self.advertised_prefix_count = state["advertised_prefix_count"]
            if self.bgp_state == BGPState.ESTABLISHED:
                self.last_established_state = timezone.now()
            self.save()
            return True

        return False


class InternetExchange(AbstractGroup):
    peeringdb_ixlan = models.ForeignKey(
        to="peeringdb.IXLan", on_delete=models.SET_NULL, blank=True, null=True
    )
    ixapi_endpoint = models.ForeignKey(
        to="extras.IXAPI",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="IX-API",
        help_text="URL and authentication details to interact with IX-API",
    )
    local_autonomous_system = models.ForeignKey(
        to="peering.AutonomousSystem", on_delete=models.CASCADE, null=True
    )
    contacts = GenericRelation(to="messaging.ContactAssignment")

    class Meta(AbstractGroup.Meta):
        ordering = ["local_autonomous_system", "name", "slug"]
        permissions = [
            (
                "view_internet_exchange_point_ixapi",
                "Can view IX-API related info (read-only)",
            ),
            (
                "change_internet_exchange_point_ixapi",
                "Can use IX-API to change info (read-write)",
            ),
        ]

    @property
    def linked_to_peeringdb(self):
        """
        Tells if the PeeringDB object for this IX still exists.
        """
        return self.peeringdb_ixlan is not None

    @property
    def has_connected_routers(self):
        return (
            Connection.objects.filter(
                internet_exchange_point=self, router__isnull=False
            ).count()
            > 0
        )

    @property
    def peeringdb_prefixes(self):
        prefixes = {}

        for p in self.get_prefixes():
            prefixes.setdefault(f"ipv{p.prefix.version}", []).append(str(p.prefix))

        return prefixes

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("peering:internetexchange_view", args=[self.pk])

    def get_peering_sessions_list_url(self):
        return reverse("peering:internetexchange_peering_sessions", args=[self.pk])

    def get_peer_list_url(self):
        return reverse("peering:internet_exchange_peers", args=[self.pk])

    def merged_export_policies(self, reverse=False):
        # Get own policies
        policies = list(self.export_policies())
        return list(reversed(policies)) if reverse else policies

    def merged_import_policies(self, reverse=False):
        # Get own policies
        policies = list(self.import_policies())
        return list(reversed(policies)) if reverse else policies

    def link_to_peeringdb(self):
        """
        Retrieves the PeeringDB IDs for this IX based on connections.

        The PeeringDB records will be returned on success. In any other cases `None`
        will be returned. The value will also be saved in model's field.
        """
        peeringdb_ixlan = None
        for connection in Connection.objects.filter(internet_exchange_point=self):
            # For each connection, try to see if a valid PeeringDB record exists and
            # make sure that they all point towards the same IX
            if connection.linked_to_peeringdb:
                if peeringdb_ixlan is None:
                    peeringdb_ixlan = connection.peeringdb_netixlan.ixlan
                elif peeringdb_ixlan != connection.peeringdb_netixlan.ixlan:
                    # Connections not belonging to the same IX
                    return None

        if peeringdb_ixlan is not None:
            self.peeringdb_ixlan = peeringdb_ixlan
            self.save()
            logger.debug(f"linked ixp {self} (pk: {self.pk}) to peeringdb")

        return peeringdb_ixlan

    def get_prefixes(self, family=0):
        """
        Returns all prefixes found (in PeeringDB) for this IXP.
        """
        if not self.linked_to_peeringdb:
            return IXLanPrefix.objects.none()

        prefixes = IXLanPrefix.objects.filter(ixlan=self.peeringdb_ixlan)
        if family in (4, 6):
            return prefixes.filter(prefix__family=family)
        return prefixes

    def get_connections(self):
        """
        Returns all connections to this IXP.
        """
        return Connection.objects.filter(internet_exchange_point=self)

    def get_routers(self):
        from devices.models import Router

        return Router.objects.filter(
            pk__in=self.get_connections().values_list("router", flat=True)
        )

    def get_peering_sessions(self):
        """
        Returns all peering sessions setup over this IXP.
        """
        return InternetExchangePeeringSession.objects.filter(
            ixp_connection__in=self.get_connections()
        )

    def get_autonomous_systems(self):
        """
        Returns all autonomous systems with setup peering sessions over this IXP.
        """
        return AutonomousSystem.objects.filter(
            pk__in=self.get_peering_sessions().values_list(
                "autonomous_system", flat=True
            )
        )

    def get_available_peers(self):
        """
        Finds available peers for the AS connected to this IX.
        """
        # Not linked to PeeringDB, cannot determine peers
        if not self.linked_to_peeringdb:
            return NetworkIXLan.objects.none()

        # To rule out an IP from the list it *must* appear one time per connection
        # Maybe the following code block can be optimised for better performances
        # First, fetch all sessions for each connection
        ip_addresses_per_connection = []
        for connection in self.get_connections():
            ip_addresses_per_connection.append(
                InternetExchangePeeringSession.objects.filter(
                    ixp_connection=connection
                ).values_list("ip_address", flat=True)
            )
        # Intersect all lists to find common sessions, these sessions can be excluded
        # from the lookup performed after this
        ip_addresses = list(set.intersection(*map(set, ip_addresses_per_connection)))

        return NetworkIXLan.objects.filter(
            ~Q(asn=self.local_autonomous_system.asn)
            & Q(ixlan=self.peeringdb_ixlan)
            & (
                (Q(ipaddr6__isnull=False) & ~Q(ipaddr6__in=ip_addresses))
                | (Q(ipaddr4__isnull=False) & ~Q(ipaddr4__in=ip_addresses))
            )
        ).order_by("asn")

    def get_ixapi_network_service(self):
        """
        Returns data from IX-API's network service corresponding to this IXP.
        """
        if not self.ixapi_endpoint:
            return None

        candidates = self.ixapi_endpoint.get_network_services()

        # First we try to get a match using known connections if any
        networks = []
        for ipv4, ipv6 in self.get_connections().values_list(
            "ipv4_address", "ipv6_address"
        ):
            if ipv4.network not in networks:
                networks.append(ipv4.network)
            if ipv6.network not in networks:
                networks.append(ipv6.network)

        for candidate in candidates:
            # Check if prefixes between IX-API and known connections match
            if candidate.subnet_v4 in networks or candidate.subnet_v6 in networks:
                return candidate

        # Then we fall back to make a match using PeeringDB data
        network_service = None
        for candidate in candidates:
            # If PeeringDB's IX IDs match, we are on the right track
            if (
                self.peeringdb_ixlan
                and self.peeringdb_ixlan.ix.id == candidate.peeringdb_ixid
            ):
                # Check if prefixes between IX-API and PeeringDB match
                found_v4 = False
                found_v6 = False
                for i in self.get_prefixes():
                    if i.prefix == candidate.subnet_v4:
                        found_v4 = True
                    if i.prefix == candidate.subnet_v6:
                        found_v6 = True

                if found_v4 and found_v6:
                    network_service = candidate
                    break

        return network_service

    @transaction.atomic
    def import_sessions(self, connection):
        """
        Imports sessions setup on a connected router.
        """
        session_number, asn_number = 0, 0
        ignored_autonomous_systems = []

        allowed_prefixes = self.get_prefixes()
        sessions = connection.router.get_bgp_neighbors()

        def is_valid(ip_address):
            for p in allowed_prefixes:
                if p.prefix.version == ip_address.version and ip_address in p.prefix:
                    return True
            return False

        for session in sessions:
            ip = ipaddress.ip_address(session["ip_address"])
            if not is_valid(ip):
                logger.debug(
                    f"ignoring ixp session, {ip!s} does not fit in any prefixes"
                )
                continue

            logger.debug(f"processing ixp session {ip!s}")
            remote_asn = session["remote_asn"]

            try:
                InternetExchangePeeringSession.objects.get(
                    ixp_connection=connection, ip_address=ip
                )
                logger.debug(f"ixp session {ip!s} with as{remote_asn} already exists")
                continue
            except InternetExchangePeeringSession.DoesNotExist:
                logger.debug(f"ixp session {ip!s} with as{remote_asn} does not exist")

            # Get the AS, create it if needed
            autonomous_system = AutonomousSystem.create_from_peeringdb(remote_asn)

            # Do not count the AS if it does not have a PeeringDB record
            if autonomous_system:
                logger.debug(f"as{remote_asn} created")
                asn_number += 1
            elif remote_asn not in ignored_autonomous_systems:
                ignored_autonomous_systems.append(remote_asn)
                logger.debug(f"could not create as{remote_asn}, session {ip!s} ignored")

            # Only add a session if we can use the AS it is linked to
            if autonomous_system:
                logger.debug(f"creating session {ip!s}")
                InternetExchangePeeringSession.objects.create(
                    autonomous_system=autonomous_system,
                    ixp_connection=connection,
                    ip_address=ip,
                )
                session_number += 1
                logger.debug(f"session {ip!s} created")

        return session_number, asn_number


class InternetExchangePeeringSession(BGPSession):
    ixp_connection = models.ForeignKey(
        to="net.Connection",
        on_delete=models.CASCADE,
        null=True,
        verbose_name="IXP connection",
    )
    is_route_server = models.BooleanField(
        blank=True, default=False, verbose_name="Route server"
    )

    class Meta(BGPSession.Meta):
        ordering = [
            "service_reference",
            "autonomous_system",
            "ixp_connection",
            "ip_address",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["ixp_connection", "ip_address"],
                name="unique_internetexchangepeeringsession_connection_ip",
            )
        ]

    @property
    def exists_in_peeringdb(self):
        """
        Returns `True` if a `NetworkIXLan` exists for this session's IP and if
        the `NetworkIXLan` ASN matches the autonomous system's.
        """
        if isinstance(self.ip_address, str):
            ip_version = ipaddress.ip_address(self.ip_address).version
        else:
            ip_version = self.ip_address.version
        try:
            NetworkIXLan.objects.get(
                **{
                    f"ipaddr{ip_version}": str(self.ip_address),
                    "net__asn": self.autonomous_system.asn,
                }
            )
        except NetworkIXLan.DoesNotExist:
            return False
        return True

    @property
    def is_abandoned(self):
        """
        Returns `True` if a session is considered as abandoned. Returns
        `False` otherwise.

        A session is *not* considered as abandoned if it matches one of the following
        criteria:
          * The `InternetExchange` is not linked to a PeeringDB record
          * User does not poll peering session states
          * The peer AS has no cached PeeringDB record
          * The peer AS has a cached PeeringDB record with the session IP address
          * The BGP state for the session is not idle or active
        """
        return not (
            not self.ixp_connection.linked_to_peeringdb
            or (
                self.ixp_connection.router
                and not self.ixp_connection.router.poll_bgp_sessions_state
            )
            or not self.autonomous_system.peeringdb_network
            or self.exists_in_peeringdb
            or self.bgp_state not in [BGPState.IDLE, BGPState.ACTIVE]
        )

    @staticmethod
    def create_from_peeringdb(affiliated, internet_exchange, netixlan):
        results = []

        if not netixlan:
            return results

        # If the IXP is not given, e.g. we are in the provisionning section, try to
        # guess the IXP from the PeeringDB record
        if not internet_exchange:
            internet_exchange = InternetExchange.objects.filter(
                local_autonomous_system=affiliated, peeringdb_ixlan=netixlan.ixlan
            ).first()
        available_connections = Connection.objects.filter(
            internet_exchange_point=internet_exchange
        )

        for connection in available_connections:
            for version in (6, 4):
                ip_address = getattr(netixlan, f"ipaddr{version}", None)
                if not ip_address:
                    continue

                params = {
                    "autonomous_system": AutonomousSystem.create_from_peeringdb(
                        netixlan.asn
                    ),
                    "ixp_connection": connection,
                    "ip_address": ip_address.ip,
                }

                try:
                    # Try to get the session, in case it already exists
                    InternetExchangePeeringSession.objects.get(**params)
                except InternetExchangePeeringSession.DoesNotExist:
                    results.append(InternetExchangePeeringSession(**params))

        return results

    def __str__(self):
        if not self.ixp_connection:
            return f"AS{self.autonomous_system.asn} - IP {self.ip_address}"
        return f"{self.ixp_connection.internet_exchange_point.name} - AS{self.autonomous_system.asn} - IP {self.ip_address}"

    def get_absolute_url(self):
        return reverse("peering:internetexchangepeeringsession_view", args=[self.pk])

    def poll(self):
        if not self.ixp_connection.router:
            logger.debug(
                f"cannot poll bgp session state for {self.ip_address}, no router"
            )
            return False

        state = self.ixp_connection.router.poll_bgp_session(self.ip_address)
        if state:
            self.bgp_state = state["bgp_state"]
            self.received_prefix_count = state["received_prefix_count"]
            self.accepted_prefix_count = state["accepted_prefix_count"]
            self.advertised_prefix_count = state["advertised_prefix_count"]
            if self.bgp_state == BGPState.ESTABLISHED:
                self.last_established_state = timezone.now()
            self.save()
            return True

        return False


class RoutingPolicy(OrganisationalModel):
    type = models.CharField(
        max_length=50,
        choices=RoutingPolicyType,
        default=RoutingPolicyType.IMPORT,
    )
    weight = models.PositiveSmallIntegerField(
        default=0, help_text="The higher the number, the higher the priority"
    )
    address_family = models.PositiveSmallIntegerField(
        default=IPFamily.ALL, choices=IPFamily
    )
    communities = models.ManyToManyField("Community", blank=True)

    class Meta:
        verbose_name_plural = "routing policies"
        ordering = ["-weight", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("peering:routingpolicy_view", args=[self.pk])

    def get_type_html(self, display_name=False):
        if self.type == RoutingPolicyType.EXPORT:
            badge_type = "text-bg-primary"
            text = self.get_type_display()
        elif self.type == RoutingPolicyType.IMPORT:
            badge_type = "text-bg-info"
            text = self.get_type_display()
        elif self.type == RoutingPolicyType.IMPORT_EXPORT:
            badge_type = "text-bg-dark"
            text = self.get_type_display()
        else:
            badge_type = "text-bg-secondary"
            text = "Unknown"

        if display_name:
            text = self.name

        return mark_safe(f'<span class="badge {badge_type}">{text}</span>')
