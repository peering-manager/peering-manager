import logging

from django.core.management.base import BaseCommand

from peering.models import AutonomousSystem


class Command(BaseCommand):
    help = "Get prefixes of Autonomous Systems with IRR AS-SETs and store them in the database"
    logger = logging.getLogger("peering.manager.peering")

    def handle(self, *args, **options):
        self.logger.info("Getting prefixes for AS with IRR AS-SETs")

        for autonomous_system in AutonomousSystem.objects.all():
            autonomous_system.prefixes = (
                autonomous_system.retrieve_irr_as_set_prefixes()
            )
            autonomous_system.save()
