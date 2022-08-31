from django.core.management.base import BaseCommand

from peering.models import AutonomousSystem


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

        if not quiet:
            self.stdout.write("[*] Fetching prefixes for autonomous systems")

        for autonomous_system in AutonomousSystem.objects.defer("prefixes"):
            if not quiet:
                self.stdout.write(f"  - AS{autonomous_system.asn}:")

            prefixes = autonomous_system.retrieve_irr_as_set_prefixes()
            for family in ("ipv6", "ipv4"):
                count = len(prefixes[family])

                if limit and count > limit:
                    if not quiet:
                        self.stdout.write(
                            f"    {count:>6} {family} (ignored)", self.style.WARNING
                        )
                    prefixes[family] = []
                else:
                    if not quiet:
                        self.stdout.write(
                            f"    {count:>6} {family}", self.style.SUCCESS
                        )

            autonomous_system.prefixes = prefixes
            autonomous_system.save()
