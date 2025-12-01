from __future__ import annotations

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from django.conf import settings
from django.core.exceptions import ValidationError

if TYPE_CHECKING:
    from collections.abc import Sequence
    from ipaddress import IPv4Interface, IPv6Interface

logger = logging.getLogger("peering.manager.peering")


class UnresolvableIRRObjectError(Exception):
    """Exception raised when an IRR object cannot be resolved."""

    def __init__(
        self, object: str, address_family: Literal[4, 6] | None = None, reason: str = ""
    ):
        super().__init__()
        self.object = object
        self.address_family = address_family
        self.reason = reason


def _is_using_bgpq4() -> bool:
    return Path(settings.BGPQ3_PATH).name == "bgpq4"


def _call_bgpq_binary(command: Sequence[str]) -> str:
    logger.debug(f"calling {settings.BGPQ3_PATH} with command: {' '.join(command)}")

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
        error_message = f"calling {settings.BGPQ3_PATH} with command '{' '.join(command)}' failed: {exc!s}"
        logger.error(error_message)
        raise UnresolvableIRRObjectError(
            object=as_set, address_family=address_family, reason=error_message
        ) from exc

    return list(json.loads(out)["prefix_list"])


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
        error_message = f"calling {settings.BGPQ3_PATH} with command '{' '.join(command)}' failed: {exc!s}"
        logger.error(error_message)
        raise UnresolvableIRRObjectError(object=as_set, reason=error_message) from exc

    # Always add the first ASN, and remove AS_TRANS
    return sorted(
        {first_as} | {int(i) for i in list(json.loads(out)["as_list"])} - {23456}
    )


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
