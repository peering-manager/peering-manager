from django.core.management.base import BaseCommand

from extras.models import JobResult
from peering.models import AutonomousSystem
from peeringdb.jobs import synchronize
from peeringdb.models import Synchronization
from peeringdb.sync import PeeringDB


class Command(BaseCommand):
    help = "Cache PeeringDB data locally and update AS data."

    def add_arguments(self, parser):
        parser.add_argument(
            "-f", "--flush", action="store_true", help="Remove cached PeeringDB data"
        )
        parser.add_argument(
            "-t",
            "--tasks",
            action="store_true",
            help="Delegate PeeringDB synchronization to Redis worker process.",
        )

    def handle(self, *args, **options):
        api = PeeringDB()

        if options["flush"]:
            self.stdout.write("[*] Removing cached data")
            api.clear_local_database()
            return

        if options["tasks"]:
            job = JobResult.enqueue_job(
                synchronize, "peeringdb.synchronize", Synchronization, None
            )
            self.stdout.write(self.style.SUCCESS(f"task #{job.id}"))
        else:
            self.stdout.write("[*] Caching data locally")
            api.update_local_database(api.get_last_sync_time())

            self.stdout.write("[*] Updating AS details")
            autonomous_systems = AutonomousSystem.objects.defer("prefixes")
            for autonomous_system in autonomous_systems:
                autonomous_system.synchronize_with_peeringdb()
                if options["verbosity"] >= 2:
                    self.stdout.write(f"  - Synchronized AS{autonomous_system.asn}")
