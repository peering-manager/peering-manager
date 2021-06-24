import logging

from django.core.management.base import BaseCommand

from peering.models import AutonomousSystem


class Command(BaseCommand):
    help = "Get prefixes of Autonomous Systems with IRR AS-SETs and store them in the database"
    logger = logging.getLogger("peering.manager.peering")

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
        self.logger.info("Getting prefixes for AS with IRR AS-SETs")

        for autonomous_system in AutonomousSystem.objects.defer("prefixes"):
            try:
                prefixes = autonomous_system.retrieve_irr_as_set_prefixes()
                if (
                    "limit" in options
                    and options["limit"] is not None
                    and int(options["limit"])
                ):
                    if len(prefixes["ipv6"]) > options["limit"]:
                        self.logger.debug(
                            "Too many IPv6 prefixes for as%s: %s > %s, ignoring",
                            autonomous_system.asn,
                            len(prefixes["ipv6"]),
                            options["limit"],
                        )
                        prefixes["ipv6"] = []
                    if len(prefixes["ipv4"]) > options["limit"]:
                        self.logger.debug(
                            "Too many IPv4 prefixes for as%s: %s > %s, ignoring",
                            autonomous_system.asn,
                            len(prefixes["ipv4"]),
                            options["limit"],
                        )
                        prefixes["ipv4"] = []
            except ValueError as e:
                if options.get("ignore-errors", False):
                    self.logger.warn(
                        "Error fetching prefixes for as%s: %s", autonomous_system.asn, e
                    )
                    prefixes = dict(ipv6=[], ipv4=[])
                else:
                    raise (e)

            autonomous_system.prefixes = prefixes
            autonomous_system.save()
