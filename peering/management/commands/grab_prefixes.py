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

    def handle(self, *args, **options):
        self.logger.info("Getting prefixes for AS with IRR AS-SETs")

        for autonomous_system in AutonomousSystem.objects.all():
            prefixes = autonomous_system.retrieve_irr_as_set_prefixes()

            if "limit" in options:
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
                        len(prefixes["ipv6"]),
                        options["limit"],
                    )
                    prefixes["ipv4"] = []

            autonomous_system.prefixes = prefixes
            autonomous_system.save()
