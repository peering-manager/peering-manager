import logging

from django.core.management.base import BaseCommand
from django.template.defaultfilters import pluralize

from peering.enums import DeviceState
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
        parser.add_argument(
            "--limit",
            nargs="?",
            help="Limit the configuration to the given set of routers (comma separated).",
        )

    def handle(self, *args, **options):
        routers = Router.objects.all()
        if options["limit"]:
            routers = routers.filter(hostname__in=options["limit"].split(","))

        configured = []
        self.logger.info("Deploying configurations...")

        for r in routers:
            # Only apply configuration if the device is in an enabled state
            if r.device_state != DeviceState.ENABLED:
                self.logger.info(
                    f"{r.hostname} is in a {r.device_state} state, not applying configuration"
                )
                continue

            # Configuration can be applied only if there is a template and the router
            # is running on a supported platform
            if r.configuration_template and r.platform:
                self.logger.info(f"Configuring {r.hostname}")
                # Generate configuration and apply it something has changed
                configuration = r.generate_configuration()
                error, changes = r.set_napalm_configuration(
                    configuration, commit=options["no_commit_check"]
                )
                if not options["no_commit_check"] and not error and changes:
                    r.set_napalm_configuration(configuration, commit=True)
                    configured.append(r)
            else:
                self.logger.info(f"Ignoring {r.hostname}, no configuration to apply")

        if configured:
            self.logger.info(
                f"Configurations deployed on {len(configured)} router{pluralize(len(configured))}"
            )
        else:
            self.logger.info("No configuration changes to apply")
