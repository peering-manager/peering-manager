from django.core.management.base import BaseCommand

from core.models import Job
from devices.models import Configuration
from peering.jobs import set_napalm_configuration
from peering.models import Router


class Command(BaseCommand):
    help = "Deploy configurations on routers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-commit-check",
            action="store_true",
            help="Do not check for configuration changes before commiting them (no effect in task mode).",
        )
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
        parser.add_argument(
            "-c",
            "--config",
            type=str,
            help="Override default configuration to use for config generation/deployment. Give the name of the configuration.",
        )

    def process(
        self,
        router,
        quiet=False,
        as_task=False,
        no_commit_check=False,
        config_override="",
    ):

        # Override default configuration linked in the Router object
        if config_override:
            try:
                router.configuration_template = Configuration.objects.get(
                    name=config_override
                )
            except:
                router.configuration_template = None
                self.stdout.write(
                    self.style.ERROR(
                        f"Configuration object with name '{config_override}' not found"
                    )
                )

        if not quiet:
            self.stdout.write(f"  - {router.hostname} ... ", ending="")

        if not as_task:
            configuration = router.generate_configuration()
            error, changes = router.set_napalm_configuration(
                configuration, commit=no_commit_check
            )
            if not no_commit_check and not error and changes:
                error, _ = router.set_napalm_configuration(configuration, commit=True)

            if not quiet:
                if not error:
                    self.stdout.write(self.style.SUCCESS("success"))
                else:
                    self.stdout.write(self.style.ERROR("failed"))
        else:
            job = Job.enqueue_job(
                set_napalm_configuration,
                router,
                True,
                name="commands.configure_routers",
                object=router,
            )
            if not quiet:
                self.stdout.write(self.style.SUCCESS(f"task #{job.id}"))

    def handle(self, *args, **options):
        quiet = options["verbosity"] == 0

        # Configuration can be applied only if there is a template and the router
        # is running on a supported platform
        routers = Router.objects.filter(
            configuration_template__isnull=False, platform__isnull=False
        )
        if options["limit"]:
            routers = routers.filter(hostname__in=options["limit"].split(","))

        if not quiet:
            if options["config"]:
                self.stdout.write(
                    f"[*] Selecting configuration template '{options['config']}'"
                )

            self.stdout.write("[*] Deploying configurations")

        for r in routers:
            self.process(
                r,
                quiet=quiet,
                as_task=options["tasks"],
                no_commit_check=options["no_commit_check"],
                config_override=options["config"],
            )
