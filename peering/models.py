import ipaddress
import logging

import napalm
from cacheops import CacheMiss, cache
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from jinja2 import Environment, TemplateSyntaxError
from netfields import InetAddressField, NetManager

from netbox.api import NetBox
from peeringdb.functions import get_ixlan_prefixes, get_shared_internet_exchanges
from peeringdb.models import Network, NetworkContact, NetworkIXLan
from utils.models import ChangeLoggedModel, TaggableModel, TemplateModel
from utils.validators import AddressFamilyValidator

from . import call_irr_as_set_resolver, parse_irr_as_set
from .enums import (
    BGPRelationship,
    BGPState,
    CommunityType,
    DeviceState,
    IPFamily,
    RoutingPolicyType,
)
from .fields import ASNField, CommunityField, TTLField


class AbstractGroup(ChangeLoggedModel, TaggableModel, TemplateModel):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True, max_length=255)
    comments = models.TextField(blank=True)
    import_routing_policies = models.ManyToManyField(
        "RoutingPolicy", blank=True, related_name="%(class)s_import_routing_policies"
    )
    export_routing_policies = models.ManyToManyField(
        "RoutingPolicy", blank=True, related_name="%(class)s_export_routing_policies"
    )
    communities = models.ManyToManyField("Community", blank=True)
    check_bgp_session_states = models.BooleanField(default=False)
    bgp_session_states_update = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
        ordering = ["name", "slug"]

    def get_peering_sessions_list_url(self):
        raise NotImplementedError()

    def get_peering_sessions(self):
        raise NotImplementedError()

    def poll_peering_sessions(self):
        raise NotImplementedError()


class AutonomousSystem(ChangeLoggedModel, TaggableModel, TemplateModel):
    asn = ASNField(unique=True)
    name = models.CharField(max_length=128)
    name_peeringdb_sync = models.BooleanField(default=True)
    contact_name = models.CharField(max_length=50, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True, verbose_name="Contact E-mail")
    comments = models.TextField(blank=True)
    irr_as_set = models.CharField(max_length=255, blank=True, null=True)
    irr_as_set_peeringdb_sync = models.BooleanField(default=True)
    ipv6_max_prefixes = models.PositiveIntegerField(blank=True, default=0)
    ipv6_max_prefixes_peeringdb_sync = models.BooleanField(default=True)
    ipv4_max_prefixes = models.PositiveIntegerField(blank=True, default=0)
    ipv4_max_prefixes_peeringdb_sync = models.BooleanField(default=True)
    import_routing_policies = models.ManyToManyField(
        "RoutingPolicy", blank=True, related_name="%(class)s_import_routing_policies"
    )
    export_routing_policies = models.ManyToManyField(
        "RoutingPolicy", blank=True, related_name="%(class)s_export_routing_policies"
    )
    prefixes = models.JSONField(blank=True, null=True, editable=False)
    affiliated = models.BooleanField(default=False)

    logger = logging.getLogger("peering.manager.peering")

    class Meta:
        ordering = ["asn", "affiliated"]
        permissions = [("send_email", "Can send e-mails to AS contact")]

    @property
    def peeringdb_network(self):
        try:
            return Network.objects.get(asn=self.asn)
        except Network.DoesNotExist:
            return None

    @property
    def peeringdb_contacts(self):
        if self.peeringdb_network:
            return NetworkContact.objects.filter(net=self.peeringdb_network)
        return []

    @property
    def can_receive_email(self):
        return "" != self.contact_email or self.peeringdb_contacts

    @staticmethod
    def create_from_peeringdb(asn):
        try:
            network = Network.objects.get(asn=asn)
        except Network.DoesNotExist:
            return None

        try:
            return AutonomousSystem.objects.get(asn=network.asn)
        except AutonomousSystem.DoesNotExist:
            return AutonomousSystem.objects.create(
                **{
                    "asn": network.asn,
                    "name": network.name,
                    "irr_as_set": network.irr_as_set,
                    "ipv6_max_prefixes": network.info_prefixes6,
                    "ipv4_max_prefixes": network.info_prefixes4,
                }
            )

    def get_absolute_url(self):
        return reverse("peering:autonomoussystem_details", kwargs={"asn": self.asn})

    def get_internet_exchange_peering_sessions_list_url(self):
        return reverse(
            "peering:autonomoussystem_internet_exchange_peering_sessions",
            kwargs={"asn": self.asn},
        )

    def get_direct_peering_sessions_list_url(self):
        return reverse(
            "peering:autonomoussystem_direct_peering_sessions", kwargs={"asn": self.asn}
        )

    def get_peering_sessions(self):
        return self.internetexchangepeeringsession_set.all()

    def get_internet_exchanges(self):
        internet_exchanges = []

        for session in self.internetexchangepeeringsession_set.all():
            if session.internet_exchange not in internet_exchanges:
                internet_exchanges.append(session.internet_exchange)

        return internet_exchanges

    def get_shared_internet_exchanges(self, other):
        """
        Returns all IX this AS has with the other one.
        """
        return InternetExchange.objects.filter(
            peeringdb_ix__in=get_shared_internet_exchanges(self, other),
            local_autonomous_system=other,
        )

    def get_missing_peering_sessions(self, other, internet_exchange=None):
        """
        Returns all missing peering sessions between this AS and the other one on a
        given Internet Exchange. As we are relying on PeeringDB to discover sessions
        there are no points in doing so if the IX is not linked to a PeeringDB record.

        If the Internet Exchange is not specified then missing peering sessions will
        be returned for all shared Internet Exchanges between this and the other AS.
        """
        if self == other:
            return NetworkIXLan.objects.none()

        filter = {"autonomous_system": self}
        if internet_exchange:
            filter["internet_exchange"] = internet_exchange
        ip_sessions = [
            str(s.ip_address)
            for s in InternetExchangePeeringSession.objects.filter(**filter)
        ]

        qs_filter = Q(asn=self.asn) & (
            ~Q(ipaddr6__in=ip_sessions) | ~Q(ipaddr4__in=ip_sessions)
        )
        if internet_exchange:
            qs_filter &= Q(ixlan=internet_exchange.peeringdb_netixlan.ixlan)
        else:
            qs_filter &= Q(
                ixlan__in=[
                    ix.peeringdb_netixlan.ixlan
                    for ix in self.get_shared_internet_exchanges(other)
                ]
            )
        return NetworkIXLan.objects.filter(qs_filter)

    def get_missing_peering_sessions_on_shared_internet_exchanges(self, other):
        """
        Returns a list of dictionaries, each containing an `InternetExchange` object
        and lists of IP addresses. These addresses are the ones with which peering
        sessions have *not* been configured yet on the IX.
        """
        ix_and_sessions = []

        if self == other:
            return ix_and_sessions

        for internet_exchange in self.get_shared_internet_exchanges(other):
            missing_sessions = {"ipv6": [], "ipv4": []}
            for netixlan in self.get_missing_peering_sessions(other, internet_exchange):
                # Check the NetIXLan's IP addresses for each version to see if a
                # sessions already matches
                for version in [6, 4]:
                    ipaddr = getattr(netixlan, f"ipaddr{version}", None)
                    if ipaddr and not InternetExchangePeeringSession.objects.filter(
                        autonomous_system=self,
                        internet_exchange=internet_exchange,
                        ip_address=ipaddr,
                    ):
                        missing_sessions[f"ipv{version}"].append(ipaddr)

            ix_and_sessions.append(
                {
                    "internet_exchange": internet_exchange.to_dict(),
                    "sessions": [
                        s.to_dict()
                        for s in InternetExchangePeeringSession.objects.filter(
                            autonomous_system=self, internet_exchange=internet_exchange
                        )
                    ],
                    "missing_sessions": missing_sessions,
                }
            )

        return ix_and_sessions

    def synchronize_with_peeringdb(self):
        """
        Synchronizes AS properties with those found in PeeringDB.
        """
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
        if fallback or not prefixes["ipv6"] and not prefixes["ipv4"]:
            self.logger.debug(
                f"falling back to AS number lookup to search for {self.asn} prefixes"
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
        elif address_family == 4:
            return prefixes["ipv4"]
        else:
            return prefixes

    def get_contact_email_addresses(self):
        """
        Returns a list of all contacts with their respective e-mails addresses.
        The returned list can be used in form choice fields.
        """
        addresses = []

        # Append the contact set by the user if one has been set
        if self.contact_email:
            addresses.append(
                (
                    self.contact_email,
                    f"{self.contact_name} - {self.contact_email}"
                    if self.contact_name
                    else self.contact_email,
                )
            )

        # Append the contacts found in PeeringDB, avoid re-adding a contact if the
        # email address is the same as the one set by the user manually
        for contact in self.peeringdb_contacts:
            if contact.email and contact.email not in [a[0] for a in addresses]:
                addresses.append(
                    (
                        contact.email,
                        f"{contact.name} - {contact.email}"
                        if contact.name
                        else contact.email,
                    )
                )

        return addresses

    def get_email_context(self):
        context = {
            "autonomous_system": self.to_dict(),
            "direct_peering_sessions": [
                s.to_dict()
                for s in DirectPeeringSession.objects.filter(autonomous_system=self)
            ],
        }
        affiliated = AutonomousSystem.objects.filter(affiliated=True)

        if affiliated.count() > 1:
            # If there are more than one affiliated AS, add IX and missing sessions as
            # part of the AS dict
            context["my_as"] = []
            for a in affiliated:
                as_dict = a.to_dict()
                as_dict[
                    "internet_exchanges"
                ] = self.get_missing_peering_sessions_on_shared_internet_exchanges(a)
                context["my_as"].append(as_dict)
        else:
            # This is kept for retrocompatibility
            context["my_as"] = affiliated.first().to_dict()
            context[
                "internet_exchanges"
            ] = self.get_missing_peering_sessions_on_shared_internet_exchanges(
                affiliated.first()
            )

        return context

    def generate_email(self, email):
        return email.render(self.get_email_context())

    def __str__(self):
        return f"AS{self.asn} - {self.name}"


class BGPGroup(AbstractGroup):
    logger = logging.getLogger("peering.manager.peering")

    class Meta:
        ordering = ["name", "slug"]
        verbose_name = "BGP group"

    def get_absolute_url(self):
        return reverse("peering:bgpgroup_details", kwargs={"slug": self.slug})

    def get_peering_sessions_list_url(self):
        return reverse("peering:bgpgroup_peering_sessions", kwargs={"slug": self.slug})

    def get_peering_sessions(self):
        return self.directepeeringsession_set.all()

    def poll_peering_sessions(self):
        if not self.check_bgp_session_states:
            self.logger.debug(
                'ignoring session states for %s, reason: "check disabled"',
                self.name.lower(),
            )
            return False

        peering_sessions = DirectPeeringSession.objects.prefetch_related(
            "router"
        ).filter(bgp_group=self)
        if not peering_sessions:
            # Empty result no need to go further
            return False

        # Get BGP neighbors details from router, but only get them once
        bgp_neighbors_detail = {}
        for session in peering_sessions:
            if session.router not in bgp_neighbors_detail:
                detail = session.router.get_bgp_neighbors_detail()
                bgp_neighbors_detail.update(
                    {
                        session.router: session.router.bgp_neighbors_detail_as_list(
                            detail
                        )
                    }
                )

        if not bgp_neighbors_detail:
            # Empty result no need to go further
            return False

        with transaction.atomic():
            for router, detail in bgp_neighbors_detail.items():
                for session in detail:
                    ip_address = session["remote_address"]
                    self.logger.debug(
                        "looking for session %s in %s", ip_address, self.name.lower()
                    )

                    try:
                        peering_session = DirectPeeringSession.objects.get(
                            ip_address=ip_address, bgp_group=self, router=router
                        )

                        # Get info that we are actually looking for
                        state = session["connection_state"].lower()
                        received = session["received_prefix_count"]
                        advertised = session["advertised_prefix_count"]
                        self.logger.debug(
                            "found session %s in %s with state %s",
                            ip_address,
                            self.name.lower(),
                            state,
                        )

                        # Update fields
                        peering_session.bgp_state = state
                        peering_session.received_prefix_count = (
                            received if received > 0 else 0
                        )
                        peering_session.advertised_prefix_count = (
                            advertised if advertised > 0 else 0
                        )
                        # Update the BGP state of the session
                        if peering_session.bgp_state == BGPState.ESTABLISHED:
                            peering_session.last_established_state = timezone.now()
                        peering_session.save()
                    except DirectPeeringSession.DoesNotExist:
                        self.logger.debug(
                            "session %s in %s not found", ip_address, self.name.lower()
                        )

            # Save last session states update
            self.bgp_session_states_update = timezone.now()
            self.save()

        return True

    def __str__(self):
        return self.name


class BGPSession(ChangeLoggedModel, TaggableModel, TemplateModel):
    """
    Abstract class used to define common caracteristics of BGP sessions.

    A BGP session is always defined with the following fields:
      * an autonomous system, it can also be called a peer
      * an IP address used to establish the session
      * a plain text password
      * an encrypted version of the password if the user asked for encryption
      * a TTL for multihoping
      * an enabled or disabled status telling if the session should be
        administratively up or down
      * import routing policies to apply to prefixes sent by the remote device
      * export routing policies to apply to prefixed sent to the remote device
      * a BGP state giving the current operational state of session (it will
        remain to unkown if the is disabled)
      * a received prefix count (it will stay none if polling is disabled)
      * a advertised prefix count (it will stay none if polling is disabled)
      * a date and time record of the last established state of the session
      * comments that consist of plain text that can use the markdown format
    """

    autonomous_system = models.ForeignKey("AutonomousSystem", on_delete=models.CASCADE)
    ip_address = InetAddressField(store_prefix_length=False)
    password = models.CharField(max_length=255, blank=True, null=True)
    encrypted_password = models.CharField(max_length=255, blank=True, null=True)
    multihop_ttl = TTLField(
        blank=True,
        default=1,
        verbose_name="Multihop TTL",
        help_text="Use a value greater than 1 for BGP multihop sessions",
    )
    enabled = models.BooleanField(default=True)
    import_routing_policies = models.ManyToManyField(
        "RoutingPolicy", blank=True, related_name="%(class)s_import_routing_policies"
    )
    export_routing_policies = models.ManyToManyField(
        "RoutingPolicy", blank=True, related_name="%(class)s_export_routing_policies"
    )
    bgp_state = models.CharField(
        max_length=50, choices=BGPState.choices, blank=True, null=True
    )
    received_prefix_count = models.PositiveIntegerField(blank=True, default=0)
    advertised_prefix_count = models.PositiveIntegerField(blank=True, default=0)
    last_established_state = models.DateTimeField(blank=True, null=True)
    comments = models.TextField(blank=True)

    objects = NetManager()
    logger = logging.getLogger("peering.manager.peering")

    class Meta:
        abstract = True
        ordering = ["autonomous_system", "ip_address"]

    def poll(self):
        raise NotImplementedError

    @property
    def ip_address_version(self):
        return ipaddress.ip_address(self.ip_address).version

    def get_bgp_state_html(self):
        """
        Return an HTML element based on the BGP state.
        """
        if self.bgp_state == BGPState.IDLE:
            badge = "danger"
        elif self.bgp_state in [BGPState.CONNECT, BGPState.ACTIVE]:
            badge = "warning"
        elif self.bgp_state in [BGPState.OPENSENT, BGPState.OPENCONFIRM]:
            badge = "info"
        elif self.bgp_state == BGPState.ESTABLISHED:
            badge = "success"
        else:
            badge = "secondary"

        text = '<span class="badge badge-{}">{}</span>'.format(
            badge, self.get_bgp_state_display() or "Unknown"
        )

        return mark_safe(text)

    def encrypt_password(self, commit=True):
        """
        Sets the `encrypted_password` field if a crypto module is found for the given
        platform. The field will be set to `None` otherwise.

        Returns `True` if the encrypted password has been changed, `False` otherwise.
        """
        try:
            router = getattr(self, "router")
        except AttributeError:
            try:
                router = getattr(self.internet_exchange, "router")
            except AttributeError:
                pass

        if not router or not router.platform or not router.encrypt_passwords:
            return False

        if not self.password and self.encrypted_password:
            self.encrypted_password = ""
            if commit:
                self.save()
            return True

        if not self.encrypted_password:
            # If the password is not encrypted yet, do it
            self.encrypted_password = router.platform.encrypt_password(self.password)
        else:
            # Try to re-encrypt the encrypted password, if the resulting string is the
            # same it means the password matches the router platform algorithm
            is_up_to_date = self.encrypted_password == router.platform.encrypt_password(
                self.encrypted_password
            )
            if not is_up_to_date:
                self.encrypted_password = router.platform.encrypt_password(
                    self.password
                )

        # Check if the encrypted password matches the clear one
        # Force re-encryption if there a difference
        if self.password != router.platform.decrypt_password(self.encrypted_password):
            self.encrypted_password = router.platform.encrypt_password(self.password)

        if commit:
            self.save()
        return True


class Community(ChangeLoggedModel, TaggableModel, TemplateModel):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True, max_length=255)
    value = CommunityField(max_length=50)
    type = models.CharField(
        max_length=50, choices=CommunityType.choices, default=CommunityType.INGRESS
    )
    comments = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "communities"
        ordering = ["value", "name"]

    def get_absolute_url(self):
        return reverse("peering:community_details", kwargs={"pk": self.pk})

    def get_type_html(self):
        if self.type == CommunityType.EGRESS:
            badge_type = "badge-primary"
            text = self.get_type_display()
        elif self.type == CommunityType.INGRESS:
            badge_type = "badge-info"
            text = self.get_type_display()
        else:
            badge_type = "badge-secondary"
            text = "Unknown"

        return mark_safe(f'<span class="badge {badge_type}">{text}</span>')

    def __str__(self):
        return self.name


class DirectPeeringSession(BGPSession):
    local_autonomous_system = models.ForeignKey(
        "AutonomousSystem",
        on_delete=models.CASCADE,
        related_name="%(class)s_local_autonomous_system",
        null=True,
    )
    local_ip_address = InetAddressField(
        store_prefix_length=False, blank=True, null=True
    )
    bgp_group = models.ForeignKey(
        "BGPGroup",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="BGP Group",
    )
    relationship = models.CharField(
        max_length=50,
        choices=BGPRelationship.choices,
        help_text="Relationship with the remote peer.",
    )
    router = models.ForeignKey(
        "Router", blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["local_autonomous_system", "autonomous_system", "ip_address"]

    def get_absolute_url(self):
        return reverse("peering:directpeeringsession_details", kwargs={"pk": self.pk})

    def poll(self):
        # Check if we are able to get BGP details
        log = 'ignoring session states on {}, reason: "{}"'
        if not self.router or not self.router.platform:
            log = log.format(str(self.ip_address).lower(), "no usable router attached")
        elif self.bgp_group and not self.bgp_group.check_bgp_session_states:
            log = log.format(self.name.lower(), "check disabled")
        else:
            log = None

        # If we cannot check for BGP details, don't do anything
        if log:
            self.logger.debug(log)
            return False

        # Get BGP session detail
        bgp_neighbor_detail = self.router.get_bgp_neighbors_detail(
            ip_address=self.ip_address
        )
        if bgp_neighbor_detail:
            received = bgp_neighbor_detail["received_prefix_count"]
            advertised = bgp_neighbor_detail["advertised_prefix_count"]

            # Update fields
            self.bgp_state = bgp_neighbor_detail["connection_state"].lower()
            self.received_prefix_count = received if received > 0 else 0
            self.advertised_prefix_count = advertised if advertised > 0 else 0
            if self.bgp_state == BGPState.ESTABLISHED:
                self.last_established_state = timezone.now()
            self.save()
            return True

        return False

    def get_relationship_html(self):
        if self.relationship == BGPRelationship.CUSTOMER:
            badge_type = "badge-danger"
        elif self.relationship == BGPRelationship.PRIVATE_PEERING:
            badge_type = "badge-success"
        elif self.relationship == BGPRelationship.TRANSIT_PROVIDER:
            badge_type = "badge-primary"
        else:
            badge_type = "badge-secondary"

        return mark_safe(
            f'<span class="badge {badge_type}">{self.get_relationship_display()}</span>'
        )

    def __str__(self):
        return f"{self.get_relationship_display()} - AS{self.autonomous_system.asn} - IP {self.ip_address}"


class InternetExchange(AbstractGroup):
    peeringdb_netixlan = models.ForeignKey(
        "peeringdb.NetworkIXLan", on_delete=models.SET_NULL, blank=True, null=True
    )
    peeringdb_ix = models.ForeignKey(
        "peeringdb.InternetExchange", on_delete=models.SET_NULL, blank=True, null=True
    )
    local_autonomous_system = models.ForeignKey(
        "AutonomousSystem", on_delete=models.CASCADE, null=True
    )
    ipv6_address = InetAddressField(
        store_prefix_length=False,
        blank=True,
        null=True,
        validators=[AddressFamilyValidator(6)],
    )
    ipv4_address = InetAddressField(
        store_prefix_length=False,
        blank=True,
        null=True,
        validators=[AddressFamilyValidator(4)],
    )
    router = models.ForeignKey(
        "Router", blank=True, null=True, on_delete=models.SET_NULL
    )

    objects = NetManager()
    logger = logging.getLogger("peering.manager.peering")

    class Meta(AbstractGroup.Meta):
        ordering = ["local_autonomous_system", "name", "slug"]

    @property
    def linked_to_peeringdb(self):
        """
        Tells if the PeeringDB objects for this IX are still valid.

        This function will return `True` if the PeeringDB records for this IX are
        valid or if this IX does not have both Peering DB records set. In any other
        cases, the return value will be `False`.

        Note that both the `netixlan` and `ix` must be valid.
        """
        return self.peeringdb_netixlan is not None and self.peeringdb_ix is not None

    def get_absolute_url(self):
        return reverse("peering:internetexchange_details", kwargs={"slug": self.slug})

    def get_peering_sessions_list_url(self):
        return reverse(
            "peering:internetexchange_peering_sessions", kwargs={"slug": self.slug}
        )

    def get_peer_list_url(self):
        return reverse("peering:internet_exchange_peers", kwargs={"slug": self.slug})

    def get_peering_sessions(self):
        return self.internetexchangepeeringsession_set.all()

    def get_autonomous_systems(self):
        autonomous_systems = []

        for session in self.internetexchangepeeringsession_set.all():
            if session.autonomous_system not in autonomous_systems:
                autonomous_systems.append(session.autonomous_system)

        return autonomous_systems

    def link_to_peeringdb(self):
        """
        Retrieves the PeeringDB IDs for this IX based on the IP addresses that have
        been recorded. The PeeringDB records will be returned on success. In any other
        cases `None` will be returned. The values will also be saved in the
        corresponding fields or the model.
        """
        try:
            netixlan = NetworkIXLan.objects.get(
                ipaddr6=self.ipv6_address, ipaddr4=self.ipv4_address
            )
        except NetworkIXLan.DoesNotExist:
            return None, None

        # Set field values for future use
        self.peeringdb_netixlan = netixlan
        self.peeringdb_ix = netixlan.ixlan.ix
        self.save()

        return netixlan, netixlan.ixlan.ix

    def get_prefixes(self):
        """
        Returns a list of prefixes found in PeeringDB for this IX.
        """
        if self.peeringdb_netixlan:
            return get_ixlan_prefixes(self.peeringdb_netixlan.ixlan)
        return []

    def get_available_peers(self):
        """
        Finds available peers for the AS connected to this IX.
        """
        # Not linked to PeeringDB, cannot determine peers
        if not self.linked_to_peeringdb:
            return []

        # Get all peering sessions currently existing
        existing_sessions = self.get_peering_sessions()
        ipv6_sessions = []
        ipv4_sessions = []
        for session in existing_sessions:
            ip = ipaddress.ip_address(session.ip_address)
            if ip.version == 6:
                ipv6_sessions.append(str(ip))
            elif ip.version == 4:
                ipv4_sessions.append(str(ip))
            else:
                self.logger.debug(f"peering session with strange ip: {ip}")

        return NetworkIXLan.objects.filter(
            ~Q(asn=self.local_autonomous_system.asn)
            & Q(ixlan=self.peeringdb_netixlan.ixlan)
            & (~Q(ipaddr6__in=ipv6_sessions) | ~Q(ipaddr4__in=ipv4_sessions))
        ).order_by("asn")

    def _import_peering_sessions(self, sessions=[], prefixes=[]):
        # No sessions or no prefixes, can't work with that
        if not sessions or not prefixes:
            return None

        # Values to be returned
        number_of_peering_sessions = 0
        number_of_autonomous_systems = 0
        ignored_autonomous_systems = []

        with transaction.atomic():
            # For each session check if the address fits in one of the prefixes
            for session in sessions:
                for prefix in prefixes:
                    # No point of checking if a session fits inside a prefix if
                    # they are not using the same IP version
                    if session["ip_address"].version is not prefix.version:
                        self.logger.debug(
                            "ip %s cannot fit in prefix %s (not same ip version) ignoring",
                            str(session["ip_address"]),
                            str(prefix),
                        )
                        continue

                    self.logger.debug(
                        "checking if ip %s fits in prefix %s",
                        str(session["ip_address"]),
                        str(prefix),
                    )

                    # If the address fits, create a new InternetExchangePeeringSession
                    # object and a new AutonomousSystem object if they does not exist
                    # already
                    if session["ip_address"] in prefix:
                        ip_address = str(session["ip_address"])
                        remote_asn = session["remote_asn"]
                        self.logger.debug(
                            "ip %s fits in prefix %s", ip_address, str(prefix)
                        )

                        try:
                            InternetExchangePeeringSession.objects.get(
                                ip_address=ip_address, internet_exchange=self
                            )
                            self.logger.debug(
                                "session %s with as%s already exists",
                                ip_address,
                                remote_asn,
                            )
                        except InternetExchangePeeringSession.DoesNotExist:
                            self.logger.debug(
                                "session %s with as%s does not exist",
                                ip_address,
                                remote_asn,
                            )

                            # Grab the AS, create it if it does not exist in
                            # the database yet
                            autonomous_system = None
                            try:
                                autonomous_system = AutonomousSystem.objects.get(
                                    asn=remote_asn
                                )
                            except AutonomousSystem.DoesNotExist:
                                self.logger.debug(
                                    "as%s not present importing from peeringdb",
                                    remote_asn,
                                )
                                autonomous_system = (
                                    AutonomousSystem.create_from_peeringdb(remote_asn)
                                )

                                # Do not count the AS if it does not have a
                                # PeeringDB record
                                if autonomous_system:
                                    self.logger.debug("as%s created", remote_asn)
                                    number_of_autonomous_systems += 1
                                else:
                                    if remote_asn not in ignored_autonomous_systems:
                                        ignored_autonomous_systems.append(remote_asn)
                                    self.logger.debug(
                                        "could not create as%s, session %s ignored",
                                        remote_asn,
                                        ip_address,
                                    )

                            # Only add a peering session if we were able to
                            # actually use the AS it is linked to
                            if autonomous_system:
                                self.logger.debug("creating session %s", ip_address)
                                values = {
                                    "autonomous_system": autonomous_system,
                                    "internet_exchange": self,
                                    "ip_address": ip_address,
                                }
                                peering_session = InternetExchangePeeringSession(
                                    **values
                                )
                                peering_session.save()
                                number_of_peering_sessions += 1
                                self.logger.debug("session %s created", ip_address)
                    else:
                        self.logger.debug(
                            "ip %s do not fit in prefix %s",
                            str(session["ip_address"]),
                            str(prefix),
                        )

        return (
            number_of_autonomous_systems,
            number_of_peering_sessions,
            ignored_autonomous_systems,
        )

    def import_peering_sessions_from_router(self):
        log = 'ignoring peering session on {}, reason: "{}"'
        if not self.router:
            log = log.format(self.name.lower(), "no router attached")
        elif not self.router.platform:
            log = log.format(self.name.lower(), "router with unsupported platform")
        else:
            log = None

        # No point of discovering from router if platform is none or is not
        # supported.
        if log:
            self.logger.debug(log)
            return False

        # Build a list based on prefixes based on PeeringDB records
        prefixes = [p.prefix for p in self.get_prefixes()]
        # No prefixes found
        if not prefixes:
            self.logger.debug("no prefixes found for %s", self.name.lower())
            return None
        else:
            self.logger.debug(
                "found %s prefixes (%s) for %s",
                len(prefixes),
                ", ".join([str(prefix) for prefix in prefixes]),
                self.name.lower(),
            )

        # Gather all existing BGP sessions from the router connected to the IX
        bgp_sessions = self.router.get_bgp_neighbors()

        return self._import_peering_sessions(bgp_sessions, prefixes)

    def poll_peering_sessions(self):
        # Check if we are able to get BGP details
        log = 'ignoring session states on {}, reason: "{}"'
        if not self.router or not self.router.platform:
            log = log.format(self.name.lower(), "no usable router attached")
        elif not self.check_bgp_session_states:
            log = log.format(self.name.lower(), "check disabled")
        else:
            log = None

        # If we cannot check for BGP details, don't do anything
        if log:
            self.logger.debug(log)
            return False

        # Get all BGP sessions detail
        bgp_neighbors_detail = self.router.get_bgp_neighbors_detail()

        # An error occured, probably
        if not bgp_neighbors_detail:
            return False

        with transaction.atomic():
            for vrf, as_details in bgp_neighbors_detail.items():
                for asn, sessions in as_details.items():
                    # Check BGP sessions found
                    for session in sessions:
                        ip_address = session["remote_address"]
                        self.logger.debug(
                            "looking for session %s in %s",
                            ip_address,
                            self.name.lower(),
                        )

                        # Check if the BGP session is on this IX
                        try:
                            peering_session = (
                                InternetExchangePeeringSession.objects.get(
                                    internet_exchange=self, ip_address=ip_address
                                )
                            )
                            # Get the BGP state for the session
                            state = session["connection_state"].lower()
                            received = session["received_prefix_count"]
                            advertised = session["advertised_prefix_count"]
                            self.logger.debug(
                                "found session %s in %s with state %s",
                                ip_address,
                                self.name.lower(),
                                state,
                            )

                            # Update fields
                            peering_session.bgp_state = state
                            peering_session.received_prefix_count = (
                                received if received > 0 else 0
                            )
                            peering_session.advertised_prefix_count = (
                                advertised if advertised > 0 else 0
                            )
                            # Update the BGP state of the session
                            if peering_session.bgp_state == BGPState.ESTABLISHED:
                                peering_session.last_established_state = timezone.now()
                            peering_session.save()
                        except InternetExchangePeeringSession.DoesNotExist:
                            self.logger.debug(
                                "session %s in %s not found",
                                ip_address,
                                self.name.lower(),
                            )

            # Save last session states update
            self.bgp_session_states_update = timezone.now()
            self.save()

        return True

    def __str__(self):
        return self.name


class InternetExchangePeeringSession(BGPSession):
    internet_exchange = models.ForeignKey("InternetExchange", on_delete=models.CASCADE)
    is_route_server = models.BooleanField(blank=True, default=False)

    class Meta:
        ordering = ["autonomous_system", "ip_address"]

    @staticmethod
    def get_ix_list_for_peer_record(netixlan):
        ix_list = []
        # Find the Internet exchange given a NetworkIXLAN ID
        for ix in InternetExchange.objects.exclude(peeringdb_id__isnull=True).exclude(
            peeringdb_id=0
        ):
            # Get the IXLAN corresponding to our network
            try:
                ixlan = NetworkIXLAN.objects.get(id=ix.peeringdb_id)
            except NetworkIXLAN.DoesNotExist:
                self.logger.debug(
                    "NetworkIXLAN with ID %s not found, ignoring IX %s",
                    ix.peeringdb_id,
                    ix.name,
                )
                continue

            # Get a potentially matching IXLAN
            peer_ixlan = NetworkIXLAN.objects.filter(
                id=peer_record.network_ixlan.id, ix_id=ixlan.ix_id
            )

            # IXLAN found lets get out
            if peer_ixlan:
                ix_list.append(ix)
        return ix_list

    @staticmethod
    def create_from_peeringdb(affiliated, netixlan):
        results = []

        if not netixlan:
            return results

        internet_exchanges = InternetExchange.objects.filter(
            peeringdb_ix=netixlan.ixlan.ix, local_autonomous_system=affiliated
        )
        for internet_exchange in internet_exchanges:
            for version in [6, 4]:
                ip_address = getattr(netixlan, f"ipaddr{version}", None)
                if not ip_address:
                    continue

                params = {
                    # Create the AS, create it if necessary
                    "autonomous_system": AutonomousSystem.create_from_peeringdb(
                        netixlan.asn
                    ),
                    "internet_exchange": internet_exchange,
                    "ip_address": ip_address.ip,
                }

                try:
                    # Try to get the session, in case it already exists
                    InternetExchangePeeringSession.objects.get(**params)
                except InternetExchangePeeringSession.DoesNotExist:
                    results.append(InternetExchangePeeringSession(**params))

        return results

    def get_absolute_url(self):
        return reverse(
            "peering:internetexchangepeeringsession_details", kwargs={"pk": self.pk}
        )

    def poll(self):
        # Check if we are able to get BGP details
        log = 'ignoring session states on {}, reason: "{}"'
        if (
            not self.internet_exchange.router
            or not self.internet_exchange.router.platform
        ):
            log = log.format(str(self.ip_address).lower(), "no usable router attached")
        elif not self.internet_exchange.check_bgp_session_states:
            log = log.format(self.name.lower(), "check disabled")
        else:
            log = None

        # If we cannot check for BGP details, don't do anything
        if log:
            self.logger.debug(log)
            return False

        # Get BGP session detail
        bgp_neighbor_detail = self.internet_exchange.router.get_bgp_neighbors_detail(
            ip_address=self.ip_address
        )
        if bgp_neighbor_detail:
            received = bgp_neighbor_detail["received_prefix_count"]
            advertised = bgp_neighbor_detail["advertised_prefix_count"]

            # Update fields
            self.bgp_state = bgp_neighbor_detail["connection_state"].lower()
            self.received_prefix_count = received if received > 0 else 0
            self.advertised_prefix_count = advertised if advertised > 0 else 0
            if self.bgp_state == BGPState.ESTABLISHED:
                self.last_established_state = timezone.now()
            self.save()
            return True

        return False

    def exists_in_peeringdb(self):
        """
        Returns `True` if a NetworkIXLan exists for this session's IP.
        """
        if isinstance(self.ip_address, str):
            ip_version = ipaddress.ip_address(self.ip_address).version
        else:
            ip_version = self.ip_address.version
        try:
            NetworkIXLan.objects.get(**{f"ipaddr{ip_version}": str(self.ip_address)})
            return True
        except NetworkIXLan.DoesNotExist:
            pass
        return False

    def is_abandoned(self):
        """
        Returns True if a session is considered as abandoned. Returns False otherwise.

        A session is *not* considered as abandoned if it matches one of the following
        criteria:
          * The Internet Exchange is not linked to a PeeringDB record
          * User does not poll peering session states
          * The peer AS has no cached PeeringDB record
          * The peer AS has a cached PeeringDB record with the session IP address
          * The BGP state for the session is not idle or active
        """
        if (
            not self.internet_exchange.linked_to_peeringdb
            or not self.internet_exchange.check_bgp_session_states
            or not self.autonomous_system.peeringdb_network
            or self.exists_in_peeringdb()
            or self.bgp_state not in [BGPState.IDLE, BGPState.ACTIVE]
        ):
            return False
        return True

    def __str__(self):
        return f"{self.internet_exchange.name} - AS{self.autonomous_system.asn} - IP {self.ip_address}"


class Router(ChangeLoggedModel, TaggableModel, TemplateModel):
    local_autonomous_system = models.ForeignKey(
        "AutonomousSystem", on_delete=models.CASCADE, null=True
    )
    name = models.CharField(max_length=128)
    hostname = models.CharField(max_length=256)
    platform = models.ForeignKey(
        "devices.Platform",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text="The router platform, used to interact with it",
    )
    encrypt_passwords = models.BooleanField(
        blank=True,
        default=False,
        help_text="Try to encrypt passwords for peering sessions",
    )
    configuration_template = models.ForeignKey(
        "Configuration", blank=True, null=True, on_delete=models.SET_NULL
    )
    device_state = models.CharField(
        max_length=20,
        choices=DeviceState.choices,
        blank=True,
        help_text="State of the device for configuration pushes",
    )
    netbox_device_id = models.PositiveIntegerField(blank=True, default=0)
    use_netbox = models.BooleanField(
        blank=True,
        default=False,
        help_text="Use NetBox to communicate instead of NAPALM",
    )
    napalm_username = models.CharField(blank=True, null=True, max_length=256)
    napalm_password = models.CharField(blank=True, null=True, max_length=256)
    napalm_timeout = models.PositiveIntegerField(blank=True, default=0)
    napalm_args = models.JSONField(blank=True, null=True)
    comments = models.TextField(blank=True)

    logger = logging.getLogger("peering.manager.napalm")

    class Meta:
        ordering = ["local_autonomous_system", "name"]
        permissions = [
            ("view_router_configuration", "Can view router's configuration"),
            ("deploy_router_configuration", "Can deploy router's configuration"),
        ]

    def get_absolute_url(self):
        return reverse("peering:router_details", kwargs={"pk": self.pk})

    def get_direct_peering_sessions_list_url(self):
        return reverse("peering:router_direct_peering_sessions", kwargs={"pk": self.pk})

    def is_netbox_device(self):
        return self.netbox_device_id != 0

    def get_bgp_groups(self):
        """
        Returns BGP groups that can be deployed on this router. A group is considered
        as deployable on a router if some direct peering sessions attached to the
        group are also attached to the router.
        """
        bgp_groups = []
        for bgp_group in (
            BGPGroup.objects.all()
            .prefetch_related("communities")
            .prefetch_related("import_routing_policies")
            .prefetch_related("export_routing_policies")
            .prefetch_related("tags")
        ):
            peering_sessions = (
                DirectPeeringSession.objects.filter(bgp_group=bgp_group, router=self)
                .prefetch_related("import_routing_policies")
                .prefetch_related("export_routing_policies")
                .prefetch_related("tags")
                .prefetch_related("autonomous_system__tags")
                .prefetch_related("autonomous_system__import_routing_policies")
                .prefetch_related("autonomous_system__export_routing_policies")
                .select_related("autonomous_system")
            )
            ipv6_sessions = [
                session.to_dict()
                for session in peering_sessions.filter(ip_address__family=6)
            ]
            ipv4_sessions = [
                session.to_dict()
                for session in peering_sessions.filter(ip_address__family=4)
            ]

            # Only keep track of the BGP group if there are sessions in it
            if ipv6_sessions or ipv4_sessions:
                dict = bgp_group.to_dict()
                dict.update({"sessions": {6: ipv6_sessions, 4: ipv4_sessions}})
                bgp_groups.append(dict)
        return bgp_groups

    def get_internet_exchanges(self):
        """
        Returns Internet Exchanges attached to this router.
        """
        internet_exchanges = []
        for internet_exchange in (
            InternetExchange.objects.filter(router=self)
            .prefetch_related("communities")
            .prefetch_related("import_routing_policies")
            .prefetch_related("export_routing_policies")
            .prefetch_related("tags")
            .select_related("router")
        ):
            peering_sessions = (
                InternetExchangePeeringSession.objects.filter(
                    internet_exchange=internet_exchange
                )
                .prefetch_related("import_routing_policies")
                .prefetch_related("export_routing_policies")
                .prefetch_related("tags")
                .prefetch_related("internet_exchange__communities")
                .prefetch_related("internet_exchange__import_routing_policies")
                .prefetch_related("internet_exchange__export_routing_policies")
                .prefetch_related("internet_exchange__tags")
                .prefetch_related("autonomous_system__tags")
                .prefetch_related("autonomous_system__import_routing_policies")
                .prefetch_related("autonomous_system__export_routing_policies")
                .select_related("autonomous_system")
                .select_related("internet_exchange")
                .select_related("internet_exchange__router")
            )
            dict = internet_exchange.to_dict()
            dict.update(
                {
                    "sessions": {
                        6: [
                            session.to_dict()
                            for session in peering_sessions.filter(ip_address__family=6)
                        ],
                        4: [
                            session.to_dict()
                            for session in peering_sessions.filter(ip_address__family=4)
                        ],
                    }
                }
            )
            internet_exchanges.append(dict)
        return internet_exchanges

    def get_peering_sessions(self):
        return (
            InternetExchangePeeringSession.objects.filter(
                internet_exchange__router=self
            ).order_by("internet_exchange", "ip_address")
        ).all()

    def get_configuration_context(self):
        context = {
            "my_as": self.local_autonomous_system.to_dict(),
            "autonomous_systems": [],
            "bgp_groups": self.get_bgp_groups(),
            "internet_exchanges": self.get_internet_exchanges(),
            "routing_policies": [p.to_dict() for p in RoutingPolicy.objects.all()],
            "communities": [c.to_dict() for c in Community.objects.all()],
        }

        for group in context["bgp_groups"] + context["internet_exchanges"]:
            for session in group["sessions"][6] + group["sessions"][4]:
                if session["autonomous_system"] not in context["autonomous_systems"]:
                    context["autonomous_systems"].append(session["autonomous_system"])

        return context

    def generate_configuration(self):
        cached_config_name = f"configuration_router_{self.pk}"
        try:
            return cache.get(cached_config_name)
        except CacheMiss:
            self.logger.info("no cached configuration for %s", self.hostname)

        config = (
            self.configuration_template.render(self.get_configuration_context())
            if self.configuration_template
            else ""
        )
        if settings.REDIS and settings.CACHE_TIMEOUT:
            cache.set(cached_config_name, config, settings.CACHE_TIMEOUT)
            self.logger.info("cached configuration for %s", self.hostname)
        return config

    def get_napalm_device(self):
        if not self.platform or not self.platform.napalm_driver:
            self.logger.debug("no napalm driver defined")
            return None

        self.logger.debug('looking for napalm driver "%s"', self.platform.napalm_driver)
        try:
            # Driver found, instanciate it
            driver = napalm.get_network_driver(self.platform.napalm_driver)
            self.logger.debug('found napalm driver "%s"', self.platform.napalm_driver)

            # Merge NAPALM args: first global, then platform's, finish with router's
            args = settings.NAPALM_ARGS
            if self.platform.napalm_args:
                args.update(self.platform.napalm_args)
            if self.napalm_args:
                args.update(self.napalm_args)

            return driver(
                hostname=self.hostname,
                username=self.napalm_username or settings.NAPALM_USERNAME,
                password=self.napalm_password or settings.NAPALM_PASSWORD,
                timeout=self.napalm_timeout or settings.NAPALM_TIMEOUT,
                optional_args=args,
            )
        except napalm.base.exceptions.ModuleImportError:
            # Unable to import proper driver from napalm
            # Most probably due to a broken install
            self.logger.error(
                'no napalm driver "%s" found (not installed or does not exist)',
                self.platform,
            )
            return None

    def open_napalm_device(self, device):
        """
        Opens a connection with a device using NAPALM.

        This method returns True if the connection is properly opened or False
        in any other cases. It handles exceptions that can occur during the
        connection opening process by itself.

        It is a wrapper method mostly used for logging purpose.
        """
        success = False

        if not device:
            return success

        try:
            self.logger.debug("connecting to %s", self.hostname)
            device.open()
        except napalm.base.exceptions.ConnectionException as e:
            self.logger.error(
                'error while trying to connect to %s reason "%s"', self.hostname, e
            )
        except Exception:
            self.logger.error("error while trying to connect to %s", self.hostname)
        else:
            self.logger.debug("successfully connected to %s", self.hostname)
            success = True
        finally:
            return success

    def close_napalm_device(self, device):
        """
        Closes a connection with a device using NAPALM.

        This method returns True if the connection is properly closed or False
        if the device is not valid.

        It is a wrapper method mostly used for logging purpose.
        """
        if not device:
            return False

        device.close()
        self.logger.debug("closing connection with %s", self.hostname)

        return True

    def test_napalm_connection(self):
        """
        Opens and closes a connection with a device using NAPALM to see if it
        is possible to interact with it.

        This method returns True only if the connection opening and closing are
        both successful.
        """
        opened, alive, closed = False, False, False
        device = self.get_napalm_device()

        # Open and close the test_napalm_connection
        self.logger.debug(f"testing connection with {self.hostname}")
        opened = self.open_napalm_device(device)
        if opened:
            alive = device.is_alive()
            if alive:
                closed = self.close_napalm_device(device)

        # Issue while opening or closing the connection
        if not opened or not closed or not alive:
            self.logger.error(
                f"cannot connect to {self.hostname}, napalm functions won't work"
            )

        return opened and closed and alive

    def set_napalm_configuration(self, config, commit=False):
        """
        Tries to merge a given configuration on a device using NAPALM.

        This methods returns the changes applied to the configuration if the
        merge was successful. It will return None in any other cases.

        The optional named argument 'commit' is a boolean which is used to
        know if the changes must be commited or discarded. The default value is
        False which means that the changes will be discarded.
        """
        error, changes = None, None

        # Ensure device is enabled, we allow maintenance mode to force a config push
        if self.device_state == DeviceState.DISABLED:
            self.logger.debug(f"device: {self.name} is disabled, exiting config push")
            return "device is disabled, cannot deploy config", changes

        # Make sure there actually a configuration to merge
        if config is None or not isinstance(config, str) or not config.strip():
            self.logger.debug(f"no configuration to merge: {config}")
            error = "no configuration found to be merged"
            return error, changes

        device = self.get_napalm_device()
        opened = self.open_napalm_device(device)

        if opened:
            try:
                # Load the config
                self.logger.debug(f"merging configuration on {self.hostname}")
                device.load_merge_candidate(config=config)
                self.logger.debug(f"merged configuration\n{config}")

                # Get the config diff
                self.logger.debug(
                    f"checking for configuration changes on {self.hostname}"
                )
                changes = device.compare_config()
                self.logger.debug(f"raw napalm output\n{changes}")

                # Commit the config if required
                if commit:
                    self.logger.debug(f"commiting configuration on {self.hostname}")
                    device.commit_config()
                else:
                    self.logger.debug(f"discarding configuration on {self.hostname}")
                    device.discard_config()
            except napalm.base.exceptions.MergeConfigException as e:
                error = f'unable to merge configuration on {self.hostname} reason "{e}"'
                changes = None
                self.logger.debug(error)
            except Exception as e:
                error = f'unable to merge configuration on {self.hostname} reason "{e}"'
                changes = None
                self.logger.debug(error)
            else:
                self.logger.debug(
                    f"successfully merged configuration on {self.hostname}"
                )
            finally:
                closed = self.close_napalm_device(device)
                if not closed:
                    self.logger.debug(
                        f"error while closing connection with {self.hostname}"
                    )
        else:
            error = f"unable to connect to {self.hostname}"

        return error, changes

    def _napalm_bgp_neighbors_to_peer_list(self, napalm_dict):
        bgp_peers = []

        if not napalm_dict:
            return bgp_peers

        # For each VRF
        for vrf in napalm_dict:
            # Get peers inside it
            peers = napalm_dict[vrf]["peers"]
            self.logger.debug(
                "found %s bgp neighbors in %s vrf on %s", len(peers), vrf, self.hostname
            )

            # For each peer handle its IP address and the needed details
            for ip, details in peers.items():
                if "remote_as" not in details:
                    self.logger.debug(
                        "ignored bgp neighbor %s in %s vrf on %s",
                        ip,
                        vrf,
                        self.hostname,
                    )
                elif ip in [str(i["ip_address"]) for i in bgp_peers]:
                    self.logger.debug(
                        "duplicate bgp neighbor %s on %s", ip, self.hostname
                    )
                else:
                    try:
                        # Save the BGP session (IP and remote ASN)
                        bgp_peers.append(
                            {
                                "ip_address": ipaddress.ip_address(ip),
                                "remote_asn": details["remote_as"],
                            }
                        )
                    except ValueError as e:
                        # Error while parsing the IP address
                        self.logger.error(
                            'ignored bgp neighbor %s in %s vrf on %s reason "%s"',
                            ip,
                            vrf,
                            self.hostname,
                            e,
                        )
                        # Force next iteration
                        continue

        return bgp_peers

    def get_napalm_bgp_neighbors(self):
        """
        Returns a list of dictionaries listing all BGP neighbors found on the
        router using NAPALM.

        Each dictionary contains two keys 'ip_address' and 'remote_asn'.

        If an error occurs or no BGP neighbors can be found, the returned list
        will be empty.
        """
        bgp_sessions = []

        device = self.get_napalm_device()
        opened = self.open_napalm_device(device)

        if opened:
            # Get all BGP neighbors on the router
            self.logger.debug("getting bgp neighbors on %s", self.hostname)
            bgp_neighbors = device.get_bgp_neighbors()
            self.logger.debug("raw napalm output %s", bgp_neighbors)
            self.logger.debug(
                "found %s vrfs with bgp neighbors on %s",
                len(bgp_neighbors),
                self.hostname,
            )

            bgp_sessions = self._napalm_bgp_neighbors_to_peer_list(bgp_neighbors)
            self.logger.debug(
                "found %s bgp neighbors on %s", len(bgp_sessions), self.hostname
            )

            # Close connection to the device
            closed = self.close_napalm_device(device)
            if not closed:
                self.logger.debug(
                    "error while closing connection with %s", self.hostname
                )

        return bgp_sessions

    def get_netbox_bgp_neighbors(self):
        """
        Returns a list of dictionaries listing all BGP neighbors found on the
        router using NetBox.

        Each dictionary contains two keys 'ip_address' and 'remote_asn'.

        If an error occurs or no BGP neighbors can be found, the returned list
        will be empty.
        """
        bgp_sessions = []

        self.logger.debug("getting bgp neighbors on %s", self.hostname)
        bgp_neighbors = NetBox().napalm(self.netbox_device_id, "get_bgp_neighbors")
        self.logger.debug("raw napalm output %s", bgp_neighbors)
        self.logger.debug(
            "found %s vrfs with bgp neighbors on %s", len(bgp_neighbors), self.hostname
        )

        bgp_sessions = self._napalm_bgp_neighbors_to_peer_list(bgp_neighbors)
        self.logger.debug(
            "found %s bgp neighbors on %s", len(bgp_sessions), self.hostname
        )

        return bgp_sessions

    def get_bgp_neighbors(self):
        """
        Returns a list of dictionaries listing all BGP neighbors found on the
        router using either NAPALM or NetBox based on the use_netbox flag.

        Each dictionary contains two keys 'ip_address' and 'remote_asn'.

        If an error occurs or no BGP neighbors can be found, the returned list
        will be empty.
        """
        if self.use_netbox:
            return self.get_netbox_bgp_neighbors()
        else:
            return self.get_napalm_bgp_neighbors()

    def find_bgp_neighbor_detail(self, bgp_neighbors, ip_address):
        """
        Finds and returns a single BGP neighbor amongst others.
        """
        # NAPALM dict expected
        if not isinstance(bgp_neighbors, dict):
            return None

        # Make sure to use an IP object
        if isinstance(ip_address, str):
            ip_address = ipaddress.ip_address(ip_address)

        for _, asn in bgp_neighbors.items():
            for _, neighbors in asn.items():
                for neighbor in neighbors:
                    neighbor_ip_address = ipaddress.ip_address(
                        neighbor["remote_address"]
                    )
                    if ip_address == neighbor_ip_address:
                        return neighbor

        return None

    def get_napalm_bgp_neighbors_detail(self, ip_address=None):
        """
        Returns a list of dictionaries listing all BGP neighbors found on the
        router using NAPALM and there respective detail.

        If an error occurs or no BGP neighbors can be found, the returned list
        will be empty.
        """
        bgp_neighbors_detail = []

        device = self.get_napalm_device()
        opened = self.open_napalm_device(device)

        if opened:
            # Get all BGP neighbors on the router
            self.logger.debug("getting bgp neighbors detail on %s", self.hostname)
            bgp_neighbors_detail = device.get_bgp_neighbors_detail()
            self.logger.debug("raw napalm output %s", bgp_neighbors_detail)
            self.logger.debug(
                "found %s vrfs with bgp neighbors on %s",
                len(bgp_neighbors_detail),
                self.hostname,
            )

            # Close connection to the device
            closed = self.close_napalm_device(device)
            if not closed:
                self.logger.debug(
                    "error while closing connection with %s", self.hostname
                )

        return (
            bgp_neighbors_detail
            if not ip_address
            else self.find_bgp_neighbor_detail(bgp_neighbors_detail, ip_address)
        )

    def get_netbox_bgp_neighbors_detail(self, ip_address=None):
        """
        Returns a list of dictionaries listing all BGP neighbors found on the
        router using NetBox and their respective detail.

        If an error occurs or no BGP neighbors can be found, the returned list
        will be empty.
        """
        bgp_neighbors_detail = []

        self.logger.debug("getting bgp neighbors detail on %s", self.hostname)
        bgp_neighbors_detail = NetBox().napalm(
            self.netbox_device_id, "get_bgp_neighbors_detail"
        )
        self.logger.debug("raw napalm output %s", bgp_neighbors_detail)
        self.logger.debug(
            "found %s vrfs with bgp neighbors on %s",
            len(bgp_neighbors_detail),
            self.hostname,
        )

        return (
            bgp_neighbors_detail
            if not ip_address
            else self.find_bgp_neighbor_detail(bgp_neighbors_detail, ip_address)
        )

    def get_bgp_neighbors_detail(self, ip_address=None):
        """
        Returns a list of dictionaries listing all BGP neighbors found on the router
        using either NAPALM or NetBox depending on the use_netbox flag and their
        respective detail.

        If the `ip_address` named parameter is not `None`, only the neighbor with this
        IP address will be returned

        If an error occurs or no BGP neighbors can be found, the returned list
        will be empty.
        """
        if self.use_netbox:
            return self.get_netbox_bgp_neighbors_detail(ip_address=ip_address)
        else:
            return self.get_napalm_bgp_neighbors_detail(ip_address=ip_address)

    def bgp_neighbors_detail_as_list(self, bgp_neighbors_detail):
        """
        Returns a list based on the dict returned by calling
        get_napalm_bgp_neighbors_detail.
        """
        flattened = []

        if not bgp_neighbors_detail:
            return flattened

        for vrf in bgp_neighbors_detail:
            for asn in bgp_neighbors_detail[vrf]:
                flattened.extend(bgp_neighbors_detail[vrf][asn])

        return flattened

    def clear_bgp_neighbor_command(self, address_family=6):
        """
        Returns a command to clear a BGP neighbor based on the router's platform and
        the address family.
        """
        if address_family not in [6, 4]:
            return None

        if self.platform == Platform.JUNOS:
            return "clear bgp neighbor"
        if self.platform in [Platform.EOS, Platform.IOS]:
            if address_family == 6:
                return "clear ipv6 bgp"
            else:
                return "clear ip bgp"
        if self.platform == Platform.IOSXR:
            return "clear bgp"

        return None

    def clear_bgp_session(self, bgp_session):
        if not bgp_session or not isinstance(bgp_session, BGPSession):
            self.logger.debug("no bgp session to clear")
            return None
        if not self.clear_bgp_neighbor_command:
            self.logger.debug("no command found to clear bgp session")
            return None

        device = self.get_napalm_device()
        opened = self.open_napalm_device(device)

        if opened:
            # Send command to clear the BGP neighbor
            address = ipaddress.ip_address(bgp_session.ip_address)
            command = "{} {}".format(
                self.clear_bgp_neighbor_command(address_family=address.version),
                str(address),
            )
            self.logger.debug("clearing bgp neighbor %s", str(address))
            result = device.cli([command])
            self.logger.debug("raw napalm output %s", result)

            # Close connection to the device
            closed = self.close_napalm_device(device)
            if not closed:
                self.logger.debug(
                    "error while closing connection with %s", self.hostname
                )

            return result[command]

        return None

    def __str__(self):
        return self.name


class RoutingPolicy(ChangeLoggedModel, TaggableModel, TemplateModel):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True, max_length=255)
    type = models.CharField(
        max_length=50,
        choices=RoutingPolicyType.choices,
        default=RoutingPolicyType.IMPORT,
    )
    weight = models.PositiveSmallIntegerField(
        default=0, help_text="The higher the number, the higher the priority"
    )
    address_family = models.PositiveSmallIntegerField(
        default=IPFamily.ALL, choices=IPFamily.choices
    )
    comments = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "routing policies"
        ordering = ["-weight", "name"]

    def get_absolute_url(self):
        return reverse("peering:routingpolicy_details", kwargs={"pk": self.pk})

    def get_type_html(self, display_name=False):
        if self.type == RoutingPolicyType.EXPORT:
            badge_type = "badge-primary"
            text = self.get_type_display()
        elif self.type == RoutingPolicyType.IMPORT:
            badge_type = "badge-info"
            text = self.get_type_display()
        elif self.type == RoutingPolicyType.IMPORT_EXPORT:
            badge_type = "badge-dark"
            text = self.get_type_display()
        else:
            badge_type = "badge-secondary"
            text = "Unknown"

        if display_name:
            text = self.name

        return mark_safe(f'<span class="badge {badge_type}">{text}</span>')

    def __str__(self):
        return self.name


class Template(ChangeLoggedModel, TaggableModel):
    name = models.CharField(max_length=128)
    template = models.TextField()
    comments = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def render(self, variables):
        raise NotImplementedError()

    def render_preview(self):
        raise NotImplementedError()

    def __str__(self):
        return self.name


class Configuration(Template):
    def get_absolute_url(self):
        return reverse("peering:configuration_details", kwargs={"pk": self.pk})

    def render(self, variables):
        """
        Render the template using Jinja2.
        """
        environment = Environment()

        def prefix_list(asn, address_family=0):
            """
            Return the prefixes for the given AS.
            """
            if not asn:
                return []
            autonomous_system = AutonomousSystem.objects.get(asn=asn)
            return autonomous_system.get_irr_as_set_prefixes(address_family)

        def cisco_password(password):
            from utils.crypto.cisco import MAGIC as CISCO_MAGIC

            if password.startswith(CISCO_MAGIC):
                return password[2:]
            return password

        # Add custom filters to our environment
        environment.filters["prefix_list"] = prefix_list
        environment.filters["cisco_password"] = cisco_password

        # Try rendering the template, return a message about syntax issues if there
        # are any
        try:
            jinja2_template = environment.from_string(self.template)
            return jinja2_template.render(variables)
        except TemplateSyntaxError as e:
            return f"Syntax error in template at line {e.lineno}: {e.message}"
        except Exception as e:
            return str(e)

    def render_preview(self):
        """
        Render the template using Jinja2 for previewing it.
        """
        variables = None

        # Variables for template preview
        my_as = AutonomousSystem(
            asn=64500,
            name="My AS",
            ipv6_max_prefixes=50,
            ipv4_max_prefixes=100,
            affiliated=True,
        )
        a_s = AutonomousSystem(
            asn=64501, name="ACME", ipv6_max_prefixes=50, ipv4_max_prefixes=100
        )
        a_s.tags = ["foo", "bar"]
        i_x = InternetExchange(
            name="Wakanda-IX",
            slug="wakanda-ix",
            ipv6_address="2001:db8:a::ffff",
            ipv4_address="192.0.2.128",
        )
        i_x.tags = ["foo", "bar"]
        group = BGPGroup(name="Transit Providers", slug="transit")
        group.tags = ["foo", "bar"]
        dps6 = DirectPeeringSession(
            local_autonomous_system=my_as,
            autonomous_system=a_s,
            ip_address="2001:db8::1",
            relationship=BGPRelationship.TRANSIT_PROVIDER,
        )
        dps6.tags = ["foo", "bar"]
        dps4 = DirectPeeringSession(
            local_autonomous_system=my_as,
            autonomous_system=a_s,
            ip_address="192.0.2.1",
            relationship=BGPRelationship.PRIVATE_PEERING,
        )
        dps4.tags = ["foo", "bar"]
        ixps6 = InternetExchangePeeringSession(
            autonomous_system=a_s, internet_exchange=i_x, ip_address="2001:db8:a::aaaa"
        )
        ixps6.tags = ["foo", "bar"]
        ixps4 = InternetExchangePeeringSession(
            autonomous_system=a_s, internet_exchange=i_x, ip_address="192.0.2.64"
        )
        ixps4.tags = ["foo", "bar"]
        group.sessions = {6: [dps6], 4: [dps4]}
        i_x.sessions = {6: [ixps6], 4: [ixps4]}

        return self.render(
            {
                "my_as": [my_as],
                "bgp_groups": [group],
                "internet_exchanges": [i_x],
                "routing_policies": [
                    RoutingPolicy(
                        name="Export/Import None",
                        slug="none",
                        type=RoutingPolicyType.IMPORT_EXPORT,
                    )
                ],
                "communities": [Community(name="Community Transit", value="64500:1")],
            }
        )


class Email(Template):
    # While a line length should not exceed 78 characters (as per RFC2822), we allow
    # user more characters for templating and let the user to decide what he wants to
    # with this recommended limit, including not respecting it
    subject = models.CharField(max_length=512)

    def get_absolute_url(self):
        return reverse("peering:email_details", kwargs={"pk": self.pk})

    def render(self, variables):
        """
        Render the template using Jinja2.
        """
        subject = ""
        body = ""
        environment = Environment()

        try:
            jinja2_template = environment.from_string(self.subject)
            subject = jinja2_template.render(variables)
        except TemplateSyntaxError as e:
            subject = (
                f"Syntax error in subject template at line {e.lineno}: {e.message}"
            )
        except Exception as e:
            subject = str(e)

        try:
            jinja2_template = environment.from_string(self.template)
            body = jinja2_template.render(variables)
        except TemplateSyntaxError as e:
            body = f"Syntax error in body template at line {e.lineno}: {e.message}"
        except Exception as e:
            body = str(e)

        return subject, body

    def render_preview(self):
        """
        Render the template using Jinja2 for previewing it.
        """
        variables = None

        # Variables for template preview
        my_as = AutonomousSystem(
            asn=64500,
            name="My AS",
            ipv6_max_prefixes=50,
            ipv4_max_prefixes=100,
            affiliated=True,
        )
        a_s = AutonomousSystem(
            asn=64501, name="ACME", ipv6_max_prefixes=50, ipv4_max_prefixes=100
        )
        a_s.tags = ["foo", "bar"]
        i_x = InternetExchange(
            name="Wakanda-IX",
            slug="wakanda-ix",
            ipv6_address="2001:db8:a::ffff",
            ipv4_address="192.0.2.128",
        )
        i_x.tags = ["foo", "bar"]
        group = BGPGroup(name="Transit Providers", slug="transit")
        group.tags = ["foo", "bar"]
        dps6 = DirectPeeringSession(
            local_autonomous_system=my_as,
            autonomous_system=a_s,
            ip_address="2001:db8::1",
            relationship=BGPRelationship.TRANSIT_PROVIDER,
        )
        dps6.tags = ["foo", "bar"]
        dps4 = DirectPeeringSession(
            local_autonomous_system=my_as,
            autonomous_system=a_s,
            ip_address="192.0.2.1",
            relationship=BGPRelationship.PRIVATE_PEERING,
        )
        dps4.tags = ["foo", "bar"]
        ixps6 = InternetExchangePeeringSession(
            autonomous_system=a_s, internet_exchange=i_x, ip_address="2001:db8:a::aaaa"
        )
        ixps6.tags = ["foo", "bar"]
        ixps4 = InternetExchangePeeringSession(
            autonomous_system=a_s, internet_exchange=i_x, ip_address="192.0.2.64"
        )
        ixps4.tags = ["foo", "bar"]

        return self.render(
            {
                "my_as": my_as,
                "autonomous_system": a_s,
                "internet_exchanges": [
                    {
                        "internet_exchange": i_x,
                        "sessions": [],
                        "missing_sessions": {
                            "ipv6": ["2001:db8:a::aaaa"],
                            "ipv4": ["192.0.2.64"],
                        },
                    }
                ],
                "direct_peering_sessions": [dps6, dps4],
            }
        )
