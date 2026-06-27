from __future__ import annotations

from utils.enums import ChoiceSet


class BGPGroupStatus(ChoiceSet):
    ENABLED = "enabled"
    PRE_MAINTENANCE = "pre-maintenance"
    MAINTENANCE = "maintenance"
    POST_MAINTENANCE = "post-maintenance"
    DISABLED = "disabled"

    CHOICES = (
        (ENABLED, "Enabled", "success"),
        (PRE_MAINTENANCE, "Pre-maintenance", "warning"),
        (MAINTENANCE, "Maintenance", "warning"),
        (POST_MAINTENANCE, "Post-maintenance", "warning"),
        (DISABLED, "Disabled", "danger"),
    )


class BGPSessionStatus(ChoiceSet):
    REQUESTED = "requested"
    PROVISIONING = "provisioning"
    ENABLED = "enabled"
    PRE_MAINTENANCE = "pre-maintenance"
    MAINTENANCE = "maintenance"
    POST_MAINTENANCE = "post-maintenance"
    DISABLED = "disabled"
    DECOMMISSIONING = "decommissioning"
    DECOMMISSIONED = "decommissioned"

    CHOICES = (
        (REQUESTED, "Requested", "info"),
        (PROVISIONING, "Provisioning", "secondary"),
        (ENABLED, "Enabled", "success"),
        (PRE_MAINTENANCE, "Pre-maintenance", "warning"),
        (MAINTENANCE, "Maintenance", "warning"),
        (POST_MAINTENANCE, "Post-maintenance", "warning"),
        (DISABLED, "Disabled", "danger"),
        (DECOMMISSIONING, "Decommissioning", "warning"),
        (DECOMMISSIONED, "Decommissioned", "danger"),
    )


class BGPRole(ChoiceSet):
    """
    BGP roles as defined by RFC 9234.
    """

    PROVIDER = "provider"
    RS = "rs"
    RS_CLIENT = "rs-client"
    CUSTOMER = "customer"
    PEER = "peer"

    CHOICES = (
        (PROVIDER, "Provider", "primary"),
        (RS, "Route server", "info"),
        (RS_CLIENT, "Route server client", "secondary"),
        (CUSTOMER, "Customer", "success"),
        (PEER, "Peer", "warning"),
    )

    # RFC 9234 Table 1 capability codes
    CODES = {PROVIDER: 0, RS: 1, RS_CLIENT: 2, CUSTOMER: 3, PEER: 4}

    # RFC 9234 Table 2: for a given local AS role, the only allowed remote AS role.
    # The stored `bgp_role` is always the *local* AS role.
    PAIRS = {
        PROVIDER: CUSTOMER,
        CUSTOMER: PROVIDER,
        RS: RS_CLIENT,
        RS_CLIENT: RS,
        PEER: PEER,
    }

    @classmethod
    def complement(cls, role: str | None) -> str | None:
        """
        Returns the remote AS role expected to face the local AS role per RFC 9234
        Table 2, or `None` if `role` is unknown/unset.
        """
        return cls.PAIRS.get(role)

    @classmethod
    def is_valid_pair(cls, local: str | None, remote: str | None) -> bool:
        """
        Returns `True` if `(local, remote)` is an allowed RFC 9234 Table 2 role pair.
        """
        return local in cls.PAIRS and cls.PAIRS[local] == remote


class BGPState(ChoiceSet):
    IDLE = "idle"
    CONNECT = "connect"
    ACTIVE = "active"
    OPENSENT = "opensent"
    OPENCONFIRM = "openconfirm"
    ESTABLISHED = "established"

    CHOICES = (
        (IDLE, "Idle"),
        (CONNECT, "Connect"),
        (ACTIVE, "Active"),
        (OPENSENT, "OpenSent"),
        (OPENCONFIRM, "OpenConfirm"),
        (ESTABLISHED, "Established"),
    )


class PeeringRequestStatus(ChoiceSet):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REFUSED = "refused"
    CANCELLED = "cancelled"

    CHOICES = (
        (PENDING, "Pending", "info"),
        (ACCEPTED, "Accepted", "success"),
        (REFUSED, "Refused", "danger"),
        (CANCELLED, "Cancelled", "warning"),
    )


class PeeringRequestType(ChoiceSet):
    PUBLIC_PEERING = "public"
    PRIVATE_PEERING = "private"

    CHOICES = ((PUBLIC_PEERING, "Public Peering"), (PRIVATE_PEERING, "Private Peering"))


class RequestedSessionStatus(ChoiceSet):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

    CHOICES = (
        (PENDING, "Pending", "info"),
        (ACCEPTED, "Accepted", "success"),
        (REJECTED, "Rejected", "danger"),
        (CANCELLED, "Cancelled", "warning"),
    )
