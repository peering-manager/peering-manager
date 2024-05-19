from django.core.management.base import BaseCommand

from core.models import Job

from ...jobs import push_configuration_to_data_source
from ...models import Router


class Command(BaseCommand):
    help = "Push router configurations to data sources."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            nargs="?",
            help="Limit the configuration to the given set of routers (comma separated).",
        )
        parser.add_argument(
            "-t",
            "--tasks",
            action="store_true",
            help="Delegate router configuration to Redis worker process.",
        )

    def process(self, router, quiet=False, as_task=False):
        if not quiet:
            self.stdout.write(f"  - {router.hostname} ... ", ending="")

        if not as_task:
            try:
                router.push(save=True)
                if not quiet:
                    self.stdout.write(self.style.SUCCESS("success"))
            except Exception:
                if not quiet:
                    self.stdout.write(self.style.ERROR("failed"))
        else:
            job = Job.enqueue(
                push_configuration_to_data_source,
                router,
                name="commands.push_to_data_sources",
                object=router,
            )
            if not quiet:
                self.stdout.write(self.style.SUCCESS(f"task #{job.id}"))

    def handle(self, *args, **options):
        quiet = options["verbosity"] == 0

        # Configuration can be pushed for routers with a configuration template and a
        # data source
        routers = Router.objects.filter(
            configuration_template__isnull=False, data_source__isnull=False
        )
        if options["limit"]:
            routers = routers.filter(hostname__in=options["limit"].split(","))

        if not quiet:
            self.stdout.write("[*] Pushing configurations")

        for r in routers:
            self.process(r, quiet=quiet, as_task=options["tasks"])
