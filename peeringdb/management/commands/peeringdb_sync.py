import logging

from django.core.management.base import BaseCommand

from peering.models import AutonomousSystem
from peeringdb.sync import PeeringDB


class Command(BaseCommand):
    help = "Cache PeeringDB data locally."
    logger = logging.getLogger("peering.manager.peeringdb")

    def add_arguments(self, parser):
        parser.add_argument(
            "-f", "--flush", action="store_true", help="Remove cached PeeringDB data"
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self.logger.info("Removing cached data...")
            PeeringDB().clear_local_database()
            return

        self.logger.info("Caching data locally...")

        api = PeeringDB()
        api.update_local_database(api.get_last_sync_time())

        self.logger.info("Updating AS details...")

        autonomous_systems = AutonomousSystem.objects.all()
        for autonomous_system in autonomous_systems:
            autonomous_system.synchronize_with_peeringdb()
