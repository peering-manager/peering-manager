from __future__ import annotations

from ipaddress import IPv4Address

from django.conf import settings
from django.core.exceptions import ValidationError

from peering.constants import ASN_MAX, ASN_MAX_2_OCTETS

from .enums import CommunityKind

COMMUNITY_FIELD_SEPARATOR = ":"


def validate_standard_community(values: list[str]) -> None:
    if len(values) != 2:
        raise ValueError

    if any(not p.isdigit() for p in values):
        raise ValueError("Not a valid BGP community")

    asn, com = int(values[0]), int(values[1])
    if asn <= 0 or asn > ASN_MAX_2_OCTETS or com > ASN_MAX_2_OCTETS:
        raise ValueError(
            "ASN and community value must be 16-bit numbers for BGP communities"
        )


def validate_extended_community(values: list[str]) -> None:
    if len(values) != 3 or values[0] not in ("origin", "target"):
        raise ValueError

    try:
        admin = int(values[1]) if values[1].isdigit() else IPv4Address(values[1])
    except ValueError:
        raise ValueError(
            "Administrator value must be a ASN number or an IPv4 address for BGP extended communities"
        ) from None

    assigned_number_max_value = (
        ASN_MAX_2_OCTETS if int(admin) > ASN_MAX_2_OCTETS else ASN_MAX
    )
    if (
        not values[2].isdigit()
        or int(values[2]) <= 0
        or int(values[2]) > assigned_number_max_value
    ):
        raise ValueError(
            "Assigned number must be a 16-bit or 32-bit number for BGP extended communities"
        )


def validate_large_community(values: list[str]) -> None:
    if any(not p.isdigit() for p in values):
        raise ValueError(
            "Global administrator and assigned numbers must be 32-bit numbers for BGP large communities"
        )

    admin, assigned_number_1, assigned_number_2 = (int(v) for v in values)
    if admin <= 0 or admin > ASN_MAX:
        raise ValueError(
            "Global administrator must be a 32-bit number of BGP large communities"
        )
    if any(p < 0 or p > ASN_MAX for p in (assigned_number_1, assigned_number_2)):
        raise ValueError(
            "Assigned numbers must be a 32-bit numbers for BGP large communities"
        )


def get_community_kind(value: str) -> CommunityKind:
    error = f"'{value}' is not a valid BGP community string"
    if COMMUNITY_FIELD_SEPARATOR not in value:
        raise ValueError(error)

    exploded = value.split(COMMUNITY_FIELD_SEPARATOR)

    try:
        validate_standard_community(exploded)
        return CommunityKind.STANDARD
    except ValueError:
        pass

    try:
        validate_extended_community(exploded)
        return CommunityKind.EXTENDED
    except ValueError:
        pass

    try:
        validate_large_community(exploded)
        return CommunityKind.LARGE
    except ValueError:
        pass

    raise ValueError(error)


def validate_bgp_community(value: str) -> None:
    if not settings.VALIDATE_BGP_COMMUNITY_VALUE:
        return

    try:
        get_community_kind(value)
    except ValueError as e:
        raise ValidationError(
            "BGP community does not match the standard, extended or large notation",
            params={"value": value},
        ) from e
