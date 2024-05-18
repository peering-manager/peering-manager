from django.core.management.base import BaseCommand

from core.models import Job

from ...jobs import poll_bgp_sessions
from ...models import Router


class Command(BaseCommand):
    help = "Poll BGP sessions on routers."

    def add_arguments(self, parser):
        parser.add_argument(
            "-l",
            "--limit",
            nargs="?",
            help="Limit BGP session polling to the given set of routers (comma separated).",
        )
        parser.add_argument(
            "-t",
            "--tasks",
            action="store_true",
            help="Delegate BGP sessions polling to Redis worker process.",
        )

    def process(self, router, quiet=False, as_task=False):
        if not quiet:
            self.stdout.write(f"  - {router.hostname} ... ", ending="")

        if not as_task:
            success = router.poll_bgp_sessions()
            if not quiet:
                if success:
                    self.stdout.write(self.style.SUCCESS("success"))
                else:
                    self.stdout.write(self.style.ERROR("failed"))
        else:
            job = Job.enqueue(
                poll_bgp_sessions,
                router,
                name="commands.poll_bgp_sessions",
                object=router,
            )
            if not quiet:
                self.stdout.write(self.style.SUCCESS(f"task #{job.id}"))

    def handle(self, *args, **options):
        quiet = options["verbosity"] == 0
        routers = Router.objects.filter(poll_bgp_sessions_state=True)
        if options["limit"]:
            routers = routers.filter(hostname__in=options["limit"].split(","))

        if not quiet:
            self.stdout.write("[*] Polling BGP sessions state")

        for r in routers:
            self.process(r, quiet=quiet, as_task=options["tasks"])
