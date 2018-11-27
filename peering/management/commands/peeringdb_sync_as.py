from __future__ import unicode_literals

import logging

from django.core.management.base import BaseCommand

from peering.models import AutonomousSystem


class Command(BaseCommand):
    help = "Sync autonomous systems details with PeeringDB."
    logger = logging.getLogger("peering.manager.peeringdb")

    def handle(self, *args, **options):
        self.logger.info("Syncing AS details with PeeringDB...")

        autonomous_systems = AutonomousSystem.objects.all()
        for autonomous_system in autonomous_systems:
            autonomous_system.sync_with_peeringdb()
