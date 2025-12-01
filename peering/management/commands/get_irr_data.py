from typing import Any

from django.core.management.base import BaseCommand, CommandError

from peering.functions import UnresolvableIRRObjectError
from peering.models import AutonomousSystem


class Command(BaseCommand):
    help = (
        "Get prefixes and AS lists of Autonomous Systems with IRR AS-SETs and "
        "store them in the database"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-l",
            "--limit",
            type=int,
            help=(
                "Limit the number of prefixes to store. If the prefix count is over "
                "the given value, prefixes will be ignored."
            ),
        )
        parser.add_argument(
            "-a",
            "--asn",
            nargs="?",
            help="Comma seprated list of ASN to get IRR data for.",
        )

    def retrieve_prefixes(
        self, autonomous_system: AutonomousSystem, limit: int, quiet: bool
    ) -> dict[str, list[dict[str, Any]]]:
        if not autonomous_system.retrieve_prefixes:
            if not quiet:
                self.stdout.write(
                    "    skipped (prefixes retrieval disabled)", self.style.WARNING
                )
            return {"ipv6": [], "ipv4": []}

        prefixes = autonomous_system.retrieve_irr_as_set_prefixes()
        for family in ("ipv6", "ipv4"):
            count = len(prefixes[family])

            if limit and count > limit:
                if not quiet:
                    self.stdout.write(
                        f"    {count:>6} {family} (ignored)", self.style.WARNING
                    )
                prefixes[family] = []
            elif not quiet:
                self.stdout.write(f"    {count:>6} {family}", self.style.SUCCESS)

        return prefixes

    def retrieve_as_list(
        self, autonomous_system: AutonomousSystem, quiet: bool
    ) -> list[int]:
        if not autonomous_system.retrieve_as_list:
            if not quiet:
                self.stdout.write(
                    "    skipped (AS list retrieval disabled)", self.style.WARNING
                )
            return []

        as_list = autonomous_system.retrieve_irr_as_set_as_list()
        if not quiet:
            self.stdout.write(
                f"    {len(autonomous_system.as_list):>6} ASNs in list",
                self.style.SUCCESS,
            )

        return as_list

    def handle(self, *args, **options):
        limit = int(options.get("limit") or 0)
        quiet = options["verbosity"] == 0

        if not quiet:
            self.stdout.write("[*] Fetching IRR data for autonomous systems")

        autonomous_systems = AutonomousSystem.objects.all()
        if asn := options.get("asn"):
            try:
                asns = [int(a) for a in asn.split(",")]
            except ValueError as exc:
                raise CommandError(f"{asn} is not a valid list of AS numbers") from exc

            autonomous_systems = autonomous_systems.filter(asn__in=asns)

        for autonomous_system in autonomous_systems:
            if not quiet:
                self.stdout.write(f"  - AS{autonomous_system.asn}:")

            try:
                autonomous_system.prefixes = self.retrieve_prefixes(
                    autonomous_system=autonomous_system, limit=limit, quiet=quiet
                )
                autonomous_system.as_list = self.retrieve_as_list(
                    autonomous_system=autonomous_system, quiet=quiet
                )
            except UnresolvableIRRObjectError:
                continue

            autonomous_system.save(update_fields=["prefixes", "as_list"])
