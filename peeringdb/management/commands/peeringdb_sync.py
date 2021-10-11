from django.core.management.base import BaseCommand

from peering.models import AutonomousSystem
from peeringdb.sync import PeeringDB


class Command(BaseCommand):
    help = "Cache PeeringDB data locally."

    def add_arguments(self, parser):
        parser.add_argument(
            "-f", "--flush", action="store_true", help="Remove cached PeeringDB data"
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("[*] Removing cached data")
            PeeringDB().clear_local_database()
            return

        self.stdout.write("[*] Caching data locally")

        api = PeeringDB()
        api.update_local_database(api.get_last_sync_time())

        self.stdout.write("[*] Updating AS details")

        autonomous_systems = AutonomousSystem.objects.defer("prefixes")
        for autonomous_system in autonomous_systems:
            autonomous_system.synchronize_with_peeringdb()
            if options["verbosity"] >= 2:
                self.stdout.write(f"  - Synchronized AS{autonomous_system.asn}")
