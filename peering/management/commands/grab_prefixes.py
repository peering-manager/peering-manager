from django.core.management.base import BaseCommand

from peering.models import AutonomousSystem


class Command(BaseCommand):
    help = "Get prefixes of Autonomous Systems with IRR AS-SETs and store them in the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            help="Limit the number of prefixes to store. If the prefix count is over the given value, prefixes will be ignored.",
        )
        parser.add_argument(
            "--ignore-errors",
            action="store_true",
            help="Ignore errors and continue processing all ASNs",
        )

    def handle(self, *args, **options):
        self.stdout.write("[*] Getting prefixes for AS with IRR AS-SETs")

        for autonomous_system in AutonomousSystem.objects.defer("prefixes"):
            try:
                prefixes = autonomous_system.retrieve_irr_as_set_prefixes()
                if (
                    "limit" in options
                    and options["limit"] is not None
                    and int(options["limit"])
                ):
                    if len(prefixes["ipv6"]) > options["limit"]:
                        if options["verbosity"] >= 2:
                            self.stdout.write(
                                f"  - Too many IPv6 prefixes for as{autonomous_system.asn}: {len(prefixes['ipv6'])} > {options['limit']}, ignoring",
                            )
                        prefixes["ipv6"] = []
                    if len(prefixes["ipv4"]) > options["limit"]:
                        if options["verbosity"] >= 2:
                            self.stdout.write(
                                f"  - Too many IPv4 prefixes for as{autonomous_system.asn}: {len(prefixes['ipv4'])} > {options['limit']}, ignoring",
                            )
                        prefixes["ipv4"] = []
            except ValueError as e:
                if options.get("ignore-errors", False):
                    if options["verbosity"] >= 2:
                        self.stdout.write(
                            f"  - Error fetching prefixes for as{autonomous_system.asn}: {e}"
                        )
                    prefixes = dict(ipv6=[], ipv4=[])
                else:
                    raise (e)

            autonomous_system.prefixes = prefixes
            autonomous_system.save()
