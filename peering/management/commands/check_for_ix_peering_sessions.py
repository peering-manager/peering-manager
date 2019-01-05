import logging

from django.core.management.base import BaseCommand

from peering.models import AutonomousSystem


class Command(BaseCommand):
    help = "Check for potential Internet Exchange peering sessions with other Autonomous Systems"
    logger = logging.getLogger("peering.manager.peering")

    def handle(self, *args, **options):
        self.logger.info("Checking for potential Internet Exchange peering sessions...")

        for autonomous_system in AutonomousSystem.objects.all():
            autonomous_system.find_potential_ix_peering_sessions()
