from django.core.management.base import BaseCommand

from core.models import Job
from peering.models import AutonomousSystem

from ...jobs import synchronise
from ...models import Synchronisation
from ...sync import PeeringDB


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
            help="Delegate PeeringDB synchronisation to Redis worker process.",
        )

    def handle(self, *args, **options):
        quiet = options["verbosity"] == 0
        api = PeeringDB()

        if options["flush"]:
            if not quiet:
                self.stdout.write("[*] Removing cached data ... ", ending="")
            api.clear_local_database()
            if not quiet:
                self.stdout.write("done", self.style.SUCCESS)
            return

        if options["tasks"]:
            job = Job.enqueue(
                synchronise, name="peeringdb.synchronise", object_model=Synchronisation
            )
            if not quiet:
                self.stdout.write(self.style.SUCCESS(f"task #{job.id}"))
        else:
            if not quiet:
                self.stdout.write("[*] Caching data locally ... ", ending="")
            api.update_local_database(api.get_last_sync_time())
            if not quiet:
                self.stdout.write("done", self.style.SUCCESS)

            self.stdout.write("[*] Updating AS details")
            for autonomous_system in AutonomousSystem.objects.defer("prefixes"):
                if autonomous_system.is_private:
                    continue
                if not quiet:
                    self.stdout.write(f"  - AS{autonomous_system.asn} ... ", ending="")
                autonomous_system.synchronise_with_peeringdb()
                if not quiet:
                    self.stdout.write("done", self.style.SUCCESS)
