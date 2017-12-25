from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from peering.models import AutonomousSystem


class Command(BaseCommand):
    help = 'Sync known autonomous systems with PeeringDB.'

    def handle(self, *args, **options):
        autonomous_systems = AutonomousSystem.objects.all()

        print('Syncing details of autonomous systems with PeeringDB.')
        print('This might take some time.')

        for autonomous_system in autonomous_systems:
            autonomous_system.sync_with_peeringdb()
