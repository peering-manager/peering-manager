from __future__ import annotations

import json
import logging
import re
import subprocess
from ipaddress import IPv4Address, IPv4Interface, IPv6Interface
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from django.conf import settings
from django.core.exceptions import ValidationError

from .constants import ASN_MAX, ASN_MAX_2_OCTETS
from .enums import CommunityKind

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger("peering.manager.peering")


class NoPrefixesFoundError(Exception):
    """Exception raised when no prefixes are found for an IRR object."""

    def __init__(self, object: str, address_family: Literal[4, 6]):
        super().__init__()
        self.object = object
        self.address_family = address_family


def _is_using_bgpq4() -> bool:
    return Path(settings.BGPQ3_PATH).name == "bgpq4"


def _call_bgpq_binary(command: Sequence[str]) -> str:
    logger.debug(f"calling {settings.BGPQ3_PATH} with command: {command}")

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    if process.returncode != 0:
        error_log = f"{settings.BGPQ3_PATH} exit code is {process.returncode}"
        if error_message := err.decode().strip():
            error_log += f", stderr: {error_message}"
        raise ValueError(error_log)

    return out.decode()


def parse_irr_as_set(asn: int, irr_as_set: str) -> list[tuple[str, str]]:
    """
    Validate that an AS-SET is usable and split it into smaller parts if it is
    actually composed of several AS-SETs. This will return a list of tuples like
    `(<AS-SET source>,<AS-SET name>)`.
    """
    as_sets: list[tuple[str, str]] = []

    # Can't work with empty or whitespace only AS-SET
    if not irr_as_set or not irr_as_set.strip():
        return [("", f"AS{asn}")]

    unparsed = re.split(r"[/,&\s]", irr_as_set)
    for element in unparsed:
        value = element.strip()

        if not value:
            continue

        source = ""
        as_set = value

        if match := re.match(
            r"^(?P<source>{}):+\s*(?P<as_set>.+)$".format(
                settings.BGPQ3_SOURCES.replace(",", "|")
            ),
            value,
        ):
            source = match.group("source")
            as_set = match.group("as_set")

        as_set = re.sub(r"^(?:ipv4|ipv6):", "", as_set).strip()
        as_sets.append((source, as_set))

    return as_sets


def call_irr_as_set_resolver(
    as_set: str,
    source: str = "",
    address_family: Literal[4, 6] = 6,
    irr_sources_override: str = "",
    irr_ipv6_prefixes_args_override: str = "",
    irr_ipv4_prefixes_args_override: str = "",
) -> list[dict[str, Any]]:
    """
    Call a subprocess to expand the given AS-SET for an IP version.
    """
    if not as_set:
        return []

    if _is_using_bgpq4() and settings.BGPQ4_KEEP_SOURCE_IN_SET and source:
        as_set = f"{source}:{as_set}"

    # Set the arguments to pass to bgpq3/bgpq4
    command_args = []
    if address_family == 6:
        if irr_ipv6_prefixes_args_override:
            command_args = irr_ipv6_prefixes_args_override.split()
        elif settings.BGPQ3_ARGS and "ipv6" in settings.BGPQ3_ARGS:
            command_args = settings.BGPQ3_ARGS["ipv6"]
    if address_family == 4:
        if irr_ipv4_prefixes_args_override:
            command_args = irr_ipv4_prefixes_args_override.split()
        elif settings.BGPQ3_ARGS and "ipv4" in settings.BGPQ3_ARGS:
            command_args = settings.BGPQ3_ARGS["ipv4"]

    # Call bgpq with arguments to get a JSON result;
    # only include option if argument is not null
    command = [settings.BGPQ3_PATH]

    # Set host to query
    if settings.BGPQ3_HOST:
        command += ["-h", settings.BGPQ3_HOST]

    # Set sources to query
    if irr_sources_override:
        command += ["-S", irr_sources_override]
    elif settings.BGPQ3_SOURCES:
        command += ["-S", settings.BGPQ3_SOURCES]

    command += [f"-{address_family}", *command_args, "-j", "-l", "prefix_list", as_set]

    try:
        out = _call_bgpq_binary(command)
    except ValueError as exc:
        logger.error(
            f"calling {settings.BGPQ3_PATH} with command '{' '.join(command)}' failed: {exc!s}"
        )
        raise exc

    prefix_list = json.loads(out)["prefix_list"]
    if not prefix_list:
        raise NoPrefixesFoundError(object=as_set, address_family=address_family)

    return list(prefix_list)


def call_irr_as_set_as_list_resolver(
    first_as: int, as_set: str, source: str = "", irr_sources_override: str = ""
) -> list[int]:
    """
    Call a subprocess to expand the given AS-SET for an IP version into an AS path
    list. The `first_as` parameter is only used to please bgpq3/bgpq4 as the JSON
    output does not have a use for it.
    """
    if not as_set:
        return [first_as]

    if _is_using_bgpq4() and settings.BGPQ4_KEEP_SOURCE_IN_SET and source:
        as_set = f"{source}::{as_set}"

    # Set host to query
    command = [settings.BGPQ3_PATH]
    if settings.BGPQ3_HOST:
        command += ["-h", settings.BGPQ3_HOST]

    # Set sources to query
    if irr_sources_override:
        command += ["-S", irr_sources_override]
    elif settings.BGPQ3_SOURCES:
        command += ["-S", settings.BGPQ3_SOURCES]

    command += ["-j", "-l", "as_list", "-f", str(first_as), as_set]

    try:
        out = _call_bgpq_binary(command)
    except ValueError as exc:
        logger.error(
            f"calling {settings.BGPQ3_PATH} with command '{' '.join(command)}' failed: {exc!s}"
        )
        raise exc

    # Always add the first ASN, and remove AS_TRANS
    return sorted(
        {first_as} | {int(i) for i in list(json.loads(out)["as_list"])} - {23456}
    )


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


def validate_ip_address_not_network(value: IPv6Interface | IPv4Interface) -> None:
    if value.version == 6 or value.network.prefixlen >= 31:
        return

    if value.ip == value.network.network_address:
        raise ValidationError(
            f"IP address {value} is a network address, please use a host address."
        )


def validate_ip_address_not_broadcast(value: IPv6Interface | IPv4Interface) -> None:
    if value.version == 6 or value.network.prefixlen >= 31:
        return

    if value.ip == value.network.broadcast_address:
        raise ValidationError(
            f"IP address {value} is a broadcast address, please use a host address."
        )


def validate_ip_address_not_network_nor_broadcast(
    value: IPv6Interface | IPv4Interface,
) -> None:
    validate_ip_address_not_network(value)
    validate_ip_address_not_broadcast(value)
