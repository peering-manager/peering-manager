from __future__ import annotations

import ipaddress
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from django.db import transaction
from django.utils import timezone

from net.models import PrefixListEntry

from ..functions import UnresolvableIRRObjectError, call_irr_as_set_resolver, parse_irr_as_set
from ..models import AutonomousSystemPrefixListEntry

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ..models import AutonomousSystem

__all__ = (
    "BgpqPrefixSource",
    "PrefixListEntryRepository",
    "PrefixSource",
    "PrefixSpec",
    "PrefixSynchroniser",
    "build_prefix_synchroniser",
    "normalise_prefix_list_entries",
)

logger = logging.getLogger("peering.manager.peering")

PREFIX_BATCH_SIZE = 1000


def _chunked(items, size):
    items = list(items)
    for start in range(0, len(items), size):
        yield items[start : start + size]


@dataclass(frozen=True)
class PrefixSpec:
    """
    A normalised IRR prefix-list entry. Uniquely identifies a `PrefixListEntry` row and is hashable so it can be
    deduplicated and used as a key.
    """

    prefix: str
    exact: bool = False
    greater_equal: int | None = None
    less_equal: int | None = None


def normalise_prefix_list_entries(prefixes: dict[str, list[dict[str, Any]]] | None) -> set[PrefixSpec]:
    """Turn a bgpq3/bgpq4 prefix dict into a set of `PrefixSpec`."""
    entries: set[PrefixSpec] = set()
    for family in ("ipv6", "ipv4"):
        for entry in (prefixes or {}).get(family) or []:
            entries.add(
                PrefixSpec(
                    prefix=str(ipaddress.ip_network(entry["prefix"])),
                    exact=bool(entry.get("exact", False)),
                    greater_equal=entry.get("greater-equal"),
                    less_equal=entry.get("less-equal"),
                )
            )
    return entries


class PrefixSource(Protocol):
    def retrieve(self, autonomous_system: AutonomousSystem) -> dict[str, list[dict[str, Any]]]: ...


class BgpqPrefixSource:
    """Resolves an autonomous system's IRR AS-SET into a bgpq-style prefix dict."""

    def retrieve(self, autonomous_system: AutonomousSystem) -> dict[str, list[dict[str, Any]]]:
        prefixes: dict[str, list[dict[str, Any]]] = {"ipv6": [], "ipv4": []}
        if not autonomous_system.retrieve_prefixes:
            return prefixes

        # For each AS-SET try getting IPv6 and IPv4 prefixes
        for source, as_set in parse_irr_as_set(asn=autonomous_system.asn, irr_as_set=autonomous_system.irr_as_set):
            prefixes["ipv6"].extend(
                call_irr_as_set_resolver(
                    as_set=as_set,
                    source=source,
                    address_family=6,
                    irr_sources_override=autonomous_system.irr_sources_override,
                    irr_ipv6_prefixes_args_override=autonomous_system.irr_ipv6_prefixes_args_override,
                )
            )
            prefixes["ipv4"].extend(
                call_irr_as_set_resolver(
                    as_set=as_set,
                    source=source,
                    address_family=4,
                    irr_sources_override=autonomous_system.irr_sources_override,
                    irr_ipv4_prefixes_args_override=autonomous_system.irr_ipv4_prefixes_args_override,
                )
            )

        return prefixes


class PrefixListEntryRepository:
    """Owns all database access for shared `PrefixListEntry` rows and their AS links."""

    def __init__(self, *, batch_size: int = PREFIX_BATCH_SIZE) -> None:
        self._batch_size = batch_size

    def resolve(self, specs: Iterable[PrefixSpec]) -> dict[PrefixSpec, int]:
        """
        Return a `{spec: pk}` map, creating only the rows that do not exist yet so a prefix is never stored twice
        (whether it repeats within one AS or is already stored for another).
        """
        resolved: dict[PrefixSpec, int] = {}
        for chunk_items in _chunked(set(specs), self._batch_size):
            chunk = set(chunk_items)
            existing = self._lookup(chunk)
            missing = chunk - existing.keys()
            if missing:
                PrefixListEntry.objects.bulk_create(
                    [
                        PrefixListEntry(
                            prefix=spec.prefix,
                            exact=spec.exact,
                            greater_equal=spec.greater_equal,
                            less_equal=spec.less_equal,
                        )
                        for spec in missing
                    ],
                    batch_size=self._batch_size,
                    ignore_conflicts=True,
                )
                existing |= self._lookup(missing)
            resolved.update({spec: existing[spec] for spec in chunk})
        return resolved

    def _lookup(self, specs: Iterable[PrefixSpec]) -> dict[PrefixSpec, int]:
        """Map each existing spec to its pk, querying by prefix (the index's lead column)."""
        found: dict[PrefixSpec, int] = {}
        for pk, prefix, exact, greater_equal, less_equal in PrefixListEntry.objects.filter(
            prefix__in={spec.prefix for spec in specs}
        ).values_list("pk", "prefix", "exact", "greater_equal", "less_equal"):
            found[PrefixSpec(str(prefix), exact, greater_equal, less_equal)] = pk
        return {spec: found[spec] for spec in specs if spec in found}

    def replace_links(self, autonomous_system: AutonomousSystem, entry_ids: set[int]) -> None:
        """Diff the AS-to-entry links so they exactly match `entry_ids`."""
        current_ids = set(
            AutonomousSystemPrefixListEntry.objects.filter(autonomous_system=autonomous_system).values_list(
                "entry_id", flat=True
            )
        )
        for chunk in _chunked(current_ids - entry_ids, 10 * self._batch_size):
            AutonomousSystemPrefixListEntry.objects.filter(
                autonomous_system=autonomous_system, entry_id__in=chunk
            ).delete()
        AutonomousSystemPrefixListEntry.objects.bulk_create(
            [
                AutonomousSystemPrefixListEntry(autonomous_system=autonomous_system, entry_id=i)
                for i in entry_ids - current_ids
            ],
            batch_size=self._batch_size,
            ignore_conflicts=True,
        )

    def delete_orphans(self, *, chunk_size: int = 10000) -> int:
        """
        Delete entries no longer linked to any autonomous system, in bounded chunks.

        Returns the number of rows removed.
        """
        deleted = 0
        while True:
            pks = list(
                PrefixListEntry.objects.filter(autonomous_systems__isnull=True).values_list("pk", flat=True)[
                    :chunk_size
                ]
            )
            if not pks:
                break
            deleted += PrefixListEntry.objects.filter(pk__in=pks).delete()[0]
        return deleted


class PrefixSynchroniser:
    """
    Resolves an autonomous system's IRR prefixes into shared `PrefixListEntry` rows and keeps its links in sync,
    exposing a read-through accessor for consumers.
    """

    def __init__(self, *, source: PrefixSource, repository: PrefixListEntryRepository) -> None:
        self._source = source
        self._repository = repository

    def retrieve(self, autonomous_system: AutonomousSystem) -> dict[str, list[dict[str, Any]]]:
        """Fetch the current bgpq-style prefix dict from IRR sources without persisting it."""
        return self._source.retrieve(autonomous_system)

    def synchronise(
        self, autonomous_system: AutonomousSystem, prefixes: dict[str, list[dict[str, Any]]] | None = None
    ) -> None:
        """
        Sync `autonomous_system` to `prefixes` (a bgpq-style dict), retrieving them from IRR sources first.
        """
        if prefixes is None:
            prefixes = self._source.retrieve(autonomous_system)
        entry_ids = set(self._repository.resolve(normalise_prefix_list_entries(prefixes)).values())

        with transaction.atomic():
            self._repository.replace_links(autonomous_system, entry_ids)
            autonomous_system.prefixes_updated = timezone.now()
            autonomous_system.save(update_fields=["prefixes_updated"])

    def get(self, autonomous_system: AutonomousSystem, address_family: int = 0):
        """
        Return the stored prefix list, synchronising once if it has never been fetched.

        `address_family` selects a single family (6 or 4) or both otherwise. A failed lookup keeps the stored
        prefixes and leaves the AS unmarked, so that a later run retrieves them again.
        """
        if autonomous_system.prefixes_updated is None:
            try:
                self.synchronise(autonomous_system)
            except UnresolvableIRRObjectError:
                # Catch unresolvable IRR object error and log it, but do not touch existing prefixes
                logger.warning(f"cannot resolve irr objects for AS{autonomous_system.asn}, keeping the stored prefixes")

        prefixes = autonomous_system.prefixes or {"ipv6": [], "ipv4": []}
        if address_family == 6:
            return prefixes["ipv6"]
        if address_family == 4:
            return prefixes["ipv4"]
        return prefixes


def build_prefix_synchroniser() -> PrefixSynchroniser:
    return PrefixSynchroniser(source=BgpqPrefixSource(), repository=PrefixListEntryRepository())
