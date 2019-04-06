import logging

from django.core.management.base import BaseCommand

from peering.models import InternetExchange


class Command(BaseCommand):
    help = "Deploy configurations each IX having a router and a configuration template attached."
    logger = logging.getLogger("peering.manager.peering")

    def handle(self, *args, **options):
        self.logger.info("Deploying configurations...")

        for ix in InternetExchange.objects.all():
            # Only deploy config if there are at least a configuration template, a
            # router and a platform for the router
            if ix.configuration_template and ix.router and ix.router.platform:
                self.logger.info("Deploying configuration on {}".format(ix.name))

                # Generate configuration and deploy it if it changes something
                # (without any errors)
                configuration = ix.generate_configuration()
                error, changes = ix.router.set_napalm_configuration(configuration)
                if not error and changes:
                    ix.router.set_napalm_configuration(configuration, commit=True)
            else:
                self.logger.info("No configuration to deploy on {}".format(ix.name))

        self.logger.info("Configurations deployed")
