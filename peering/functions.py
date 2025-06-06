from __future__ import annotations

import json
import logging
import re
import subprocess
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError

from .constants import ASN_MAX, ASN_MAX_2_OCTETS
from .enums import CommunityKind

logger = logging.getLogger("peering.manager.peering")


def _is_using_bgpq4() -> bool:
    return Path(settings.BGPQ3_PATH).name == "bgpq4"


def call_irr_as_set_resolver(
    irr_as_set: str, irr_as_set_source: str = "", address_family: int = 6
) -> list[dict[str, Any]]:
    """
    Call a subprocess to expand the given AS-SET for an IP version.
    """
    prefixes: list[dict[str, Any]] = []

    if not irr_as_set:
        return prefixes

    # Call bgpq with arguments to get a JSON result;
    # only include option if argument is not null
    command = [settings.BGPQ3_PATH]
    if settings.BGPQ3_HOST:
        command += ["-h", settings.BGPQ3_HOST]
    if settings.BGPQ3_SOURCES:
        command += ["-S", settings.BGPQ3_SOURCES]
    command += [f"-{address_family}", "-A", "-j", "-l", "prefix_list", irr_as_set]

    # Merge user settings to command line right before the name of the prefix list
    if settings.BGPQ3_ARGS:
        index = len(command) - 3
        command[index:index] = settings.BGPQ3_ARGS[
            "ipv6" if address_family == 6 else "ipv4"
        ]

    logger.debug(f"calling {settings.BGPQ3_PATH} with command: {command}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    if process.returncode != 0:
        error_log = f"{settings.BGPQ3_PATH} exit code is {process.returncode}"
        if err and err.strip():
            error_log += f", stderr: {err}"
        raise ValueError(error_log)

    prefixes.extend(list(json.loads(out.decode())["prefix_list"]))

    return prefixes


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

        match = re.match(
            r"^(?P<source>{}):+\s*(?P<as_set>.+)$".format(
                settings.BGPQ3_SOURCES.replace(",", "|")
            ),
            value,
        )
        if match:
            source = match.group("source")
            as_set = (
                value
                if _is_using_bgpq4() and settings.BGPQ4_KEEP_SOURCE_IN_SET
                else match.group("as_set").strip()
            )
        else:
            source = ""
            as_set = value

        as_set = re.sub(r"^(?:ipv4|ipv6):", "", as_set).strip()
        as_sets.append((source, as_set))

    return as_sets


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
