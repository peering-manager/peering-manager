from django.core.management.base import BaseCommand, CommandError

from peering.models import AutonomousSystem
from peering.services import build_prefix_synchroniser


class Command(BaseCommand):
    help = "Get prefixes of Autonomous Systems with IRR AS-SETs and store them in the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "-l",
            "--limit",
            type=int,
            help="Limit the number of prefixes to store. If the prefix count is over the given value, prefixes will be ignored.",
        )

    def handle(self, *args, **options):
        limit = int(options.get("limit") or 0)
        quiet = options["verbosity"] == 0

        self.stdout.write(
            "This command is deprecated and will be removed in a future release. Use `get_irr_data` instead.",
            self.style.WARNING,
        )

        if not quiet:
            self.stdout.write("[*] Fetching prefixes for autonomous systems")

        synchroniser = build_prefix_synchroniser()
        for autonomous_system in AutonomousSystem.objects.all():
            if not quiet:
                self.stdout.write(f"  - AS{autonomous_system.asn}:")

            if not autonomous_system.retrieve_prefixes:
                if not quiet:
                    self.stdout.write("    skipped (prefixes retrieval disabled)", self.style.WARNING)
                continue

            try:
                prefixes = synchroniser.retrieve(autonomous_system)
            except ValueError as exc:
                raise CommandError(str(exc)) from exc

            for family in ("ipv6", "ipv4"):
                count = len(prefixes[family])

                if limit and count > limit:
                    if not quiet:
                        self.stdout.write(f"    {count:>6} {family} (ignored)", self.style.WARNING)
                    prefixes[family] = []
                elif not quiet:
                    self.stdout.write(f"    {count:>6} {family}", self.style.SUCCESS)

            synchroniser.synchronise(autonomous_system, prefixes)
