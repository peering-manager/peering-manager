import ipaddress
import logging

from django.db import models
from django.utils.safestring import mark_safe
from netfields import InetAddressField, NetManager

from peering.enums import BGPGroupStatus, BGPSessionStatus, BGPState, IPFamily
from peering.fields import TTLField
from utils.models import (
    ChangeLoggedMixin,
    ConfigContextMixin,
    ExportTemplatesMixin,
    TagsMixin,
)

from .mixins import PolicyMixin


class AbstractGroup(
    ChangeLoggedMixin, ConfigContextMixin, ExportTemplatesMixin, PolicyMixin, TagsMixin
):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True, max_length=255)
    status = models.CharField(
        max_length=50,
        choices=BGPGroupStatus,
        default=BGPGroupStatus.ENABLED,
    )
    comments = models.TextField(blank=True)
    import_routing_policies = models.ManyToManyField(
        "RoutingPolicy", blank=True, related_name="%(class)s_import_routing_policies"
    )
    export_routing_policies = models.ManyToManyField(
        "RoutingPolicy", blank=True, related_name="%(class)s_export_routing_policies"
    )
    communities = models.ManyToManyField("Community", blank=True)

    class Meta:
        abstract = True
        ordering = ["name", "slug"]

    def export_policies(self):
        return self.export_routing_policies.all()

    def import_policies(self):
        return self.import_routing_policies.all()

    def get_status_colour(self):
        return BGPGroupStatus.colours.get(self.status)

    def get_peering_sessions_list_url(self):
        raise NotImplementedError()

    def get_peering_sessions(self):
        raise NotImplementedError()

    def are_bgp_sessions_pollable(self):
        """
        Returns whether or not BGP sessions can be polled for the group.

        If a router has its `poll_bgp_sessions_state` property set to a boolan true,
        BGP sessions are considered as pollable. The group also needs to contain BGP
        sessions.
        """
        if self.get_peering_sessions():
            for router in self.get_routers():
                if router.poll_bgp_sessions_state and router.is_usable_for_task():
                    return True
        return False

    def poll_bgp_sessions(self):
        """
        Polls BGP sessions belonging to the group.
        """
        for router in self.get_routers():
            router.poll_bgp_sessions()


class BGPSession(
    ChangeLoggedMixin, ConfigContextMixin, ExportTemplatesMixin, PolicyMixin, TagsMixin
):
    """
    Abstract class used to define common caracteristics of BGP sessions.

    A BGP session is always defined with the following fields:
      * a unique service reference, blank or user defined
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

    service_reference = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        help_text="Optional internal service reference",
    )
    autonomous_system = models.ForeignKey(
        to="peering.AutonomousSystem", on_delete=models.CASCADE
    )
    ip_address = InetAddressField(store_prefix_length=False, verbose_name="IP address")
    status = models.CharField(
        max_length=50,
        choices=BGPSessionStatus,
        default=BGPSessionStatus.ENABLED,
    )
    password = models.CharField(max_length=255, blank=True, null=True)
    encrypted_password = models.CharField(max_length=255, blank=True, null=True)
    multihop_ttl = TTLField(
        blank=True,
        default=1,
        verbose_name="Multihop TTL",
        help_text="Use a value greater than 1 for BGP multihop sessions",
    )
    import_routing_policies = models.ManyToManyField(
        to="peering.RoutingPolicy",
        blank=True,
        related_name="%(class)s_import_routing_policies",
    )
    export_routing_policies = models.ManyToManyField(
        to="peering.RoutingPolicy",
        blank=True,
        related_name="%(class)s_export_routing_policies",
    )
    communities = models.ManyToManyField("Community", blank=True)
    bgp_state = models.CharField(max_length=50, choices=BGPState, blank=True, null=True)
    received_prefix_count = models.PositiveIntegerField(blank=True, default=0)
    advertised_prefix_count = models.PositiveIntegerField(blank=True, default=0)
    last_established_state = models.DateTimeField(blank=True, null=True)
    comments = models.TextField(blank=True)

    objects = NetManager()
    logger = logging.getLogger("peering.manager.peering")

    class Meta:
        abstract = True
        ordering = ["service_reference", "autonomous_system", "ip_address"]

    @property
    def enabled(self):
        """
        Tells if a BGP session is enabled.

        DEPRECATED: This is kept for retro-compatibility and will be removed in 2.0.
        """
        return self.status == BGPSessionStatus.ENABLED

    def __str__(self):
        return (
            self.service_reference
            or f"AS{self.autonomous_system.asn} - {self.ip_address}"
        )

    def get_status_colour(self):
        return BGPSessionStatus.colours.get(self.status)

    def _merge_policies(self, merged_policies, new_policies):
        if type(self.ip_address) in (int, str):
            ip_address = ipaddress.ip_address(self.ip_address)
        else:
            ip_address = self.ip_address

        for policy in new_policies:
            # Only merge universal policies or policies of same IP family
            if policy in merged_policies or policy.address_family not in (
                IPFamily.ALL,
                ip_address.version,
            ):
                continue
            merged_policies.append(policy)
        return merged_policies

    def export_policies(self):
        return self.export_routing_policies.all()

    def merged_export_policies(self, reverse=False):
        merged = list(self.export_policies())

        # Merge policies from nested objects (first AS, then BGP group)
        self._merge_policies(merged, self.autonomous_system.export_policies())

        group = None
        if hasattr(self, "ixp_connection"):
            group = self.ixp_connection.internet_exchange_point
        else:
            group = self.bgp_group

        if group:
            self._merge_policies(merged, group.export_policies())

        return list(reversed(merged)) if reverse else merged

    def import_policies(self):
        return self.import_routing_policies.all()

    def merged_import_policies(self, reverse=False):
        # Get own policies
        merged = list(self.import_policies())

        # Merge policies from nested objects (first AS, then BGP group)
        self._merge_policies(merged, self.autonomous_system.import_policies())

        group = None
        if hasattr(self, "ixp_connection"):
            group = self.ixp_connection.internet_exchange_point
        else:
            group = self.bgp_group

        if group:
            self._merge_policies(merged, group.import_policies())

        return list(reversed(merged)) if reverse else merged

    def merged_communities(self):
        merged = list(self.communities.all())

        for c in self.autonomous_system.communities.all():
            if c not in merged:
                merged.append(c)

        group = None
        if hasattr(self, "ixp_connection"):
            group = self.ixp_connection.internet_exchange_point
        else:
            group = self.bgp_group

        for c in group.communities.all():
            if c not in merged:
                merged.append(c)

        return merged

    def poll(self):
        raise NotImplementedError

    def get_bgp_state_html(self):
        """
        Return an HTML element based on the BGP state.
        """
        if self.bgp_state == BGPState.IDLE:
            badge = "danger"
        elif self.bgp_state in (BGPState.CONNECT, BGPState.ACTIVE):
            badge = "warning"
        elif self.bgp_state in (BGPState.OPENSENT, BGPState.OPENCONFIRM):
            badge = "info"
        elif self.bgp_state == BGPState.ESTABLISHED:
            badge = "success"
        else:
            badge = "secondary"

        return mark_safe(
            f'<span class="badge badge-{badge}">{self.get_bgp_state_display() or "Unknown"}</span>'
        )

    def encrypt_password(self, commit=True):
        """
        Sets the `encrypted_password` field if a crypto module is found for the given
        platform. The field will be set to `None` otherwise.

        Returns `True` if the encrypted password has been changed, `False` otherwise.
        """
        try:
            router = getattr(self, "router")
        except AttributeError:
            router = getattr(self.ixp_connection, "router", None)

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


class Template(ChangeLoggedMixin, TagsMixin):
    name = models.CharField(max_length=128)
    template = models.TextField()
    jinja2_trim = models.BooleanField(
        default=False, help_text="Removes new line after tag"
    )
    jinja2_lstrip = models.BooleanField(
        default=False, help_text="Strips whitespaces before block"
    )
    comments = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def render(self, variables):
        raise NotImplementedError()

    def __str__(self):
        return self.name
