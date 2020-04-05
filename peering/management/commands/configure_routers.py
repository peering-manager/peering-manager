import logging

from django.core.management.base import BaseCommand
from django.template.defaultfilters import pluralize

from peering.models import Router


class Command(BaseCommand):
    help = "Deploy configurations on routers."
    logger = logging.getLogger("peering.manager.peering")

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-commit-check",
            action="store_true",
            help="Do not check for configuration changes before commiting them.",
        )

    def handle(self, *args, **options):
        configured = []
        self.logger.info("Deploying configurations...")

        for router in Router.objects.all():
            # Configuration can be applied only if there is a template and the router
            # is running on a supported platform
            if router.configuration_template and router.platform:
                self.logger.info("Configuring %s", router.hostname)
                # Generate configuration and apply it something has changed
                configuration = router.generate_configuration()
                error, changes = router.set_napalm_configuration(
                    configuration, commit=options["no_commit_check"]
                )
                if not options["no_commit_check"] and not error and changes:
                    router.set_napalm_configuration(configuration, commit=True)
                    configured.append(router)
            else:
                self.logger.info(
                    "Ignoring %s, no configuration to apply", router.hostname
                )

        if configured:
            self.logger.info(
                "Configurations deployed on %s router%s",
                len(configured),
                pluralize(len(configured)),
            )
        else:
            self.logger.info("No configuration changes to apply")
